package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"os"
	"strings"
	"time"

	"github.com/nlopes/slack"
	"github.com/piquette/finance-go/crypto"
	"github.com/piquette/finance-go/quote"
)

type Handler interface {
	OnEvent(ev slack.RTMEvent, bot *HBot)
}

type Command interface {
	Name() string
	Help() string
	OnMessage(command string, arguments []string, user, channel string, bot *HBot) error
}

func NewHelpCommand(h *CommandMessageHandler) *HelpCommand {
	return &HelpCommand{
		handler: h,
	}
}

type HelpCommand struct {
	handler *CommandMessageHandler
}

func (c *HelpCommand) Name() string {
	return "help"
}

func (c *HelpCommand) Help() string {
	return "this"
}

func (c *HelpCommand) OnMessage(_ string, args []string, _, channel string, bot *HBot) error {
	msg := ""
	for _, c := range c.handler.commands {
		msg += fmt.Sprintf("%s: %s\n", c.Name(), c.Help())
	}

	return bot.sendMessage(msg, channel)
}

type BangCommand struct{}

func (c *BangCommand) Name() string {
	return "bang bang"
}

func (c *BangCommand) Help() string {
	return "health check"
}

func (c *BangCommand) OnMessage(command string, arguments []string, user, channel string, bot *HBot) error {
	return bot.sendMessage("bang", channel)
}

type FedCommand struct {
	Name_   string   `json:"name"`
	Help_   string   `json:"help"`
	Images  []string `json:"images"`
	Phrases []string `json:"phrases"`
}

func NewFedCommand(fedFile string) (*FedCommand, error) {
	f, err := os.Open(fedFile)
	if err != nil {
		return nil, err
	}
	dec := json.NewDecoder(f)
	fed := &FedCommand{}
	if err := dec.Decode(&fed); err != nil {
		return nil, err
	}
	return fed, nil
}

func (c *FedCommand) Name() string {
	return c.Name_
}

func (c *FedCommand) Help() string {
	return c.Help_
}

func (c *FedCommand) OnMessage(command string, arguments []string, user, channel string, bot *HBot) error {
	var phrase, image string
	if len(c.Phrases) != 0 {
		phrase = c.Phrases[rand.Intn(len(c.Phrases))]
	}
	if len(c.Images) != 0 {
		image = c.Images[rand.Intn(len(c.Images))]
	}

	attachment := slack.Attachment{
		Text:     phrase,
		ImageURL: image,
	}

	return bot.sendMessage("", channel, attachment)
}

type CoinCommand struct{}

func (c *CoinCommand) Name() string {
	return "crypto"
}

func (c *CoinCommand) Help() string {
	return "Coinbase pro crypto prices"
}

func (c *CoinCommand) OnMessage(command string, arguments []string, user, channel string, bot *HBot) error {
	msg := ""

	for _, coin := range arguments {
		q, err := crypto.Get(coin)
		if err != nil {
			msg += fmt.Sprintf("%s: %s\n", coin, err.Error())
		} else {
			msg += fmt.Sprintf("%s: %.2f", coin, q.RegularMarketPrice)
		}
	}

	return bot.sendMessage(msg, channel)
}

type StockCommand struct{}

func (c *StockCommand) Name() string {
	return "stocks"
}

func (c *StockCommand) Help() string {
	return "ticker quotes"
}

func (C *StockCommand) OnMessage(command string, arguments []string, user, channel string, bot *HBot) error {
	msg := ""
	for _, sym := range arguments {
		sym = strings.ToUpper(sym)
		q, err := quote.Get(sym)
		if err != nil {
			msg += fmt.Sprintf("%s: %s\n", sym, err.Error())
		} else {
			msg += fmt.Sprintf("%s: %.2f (open %.2f)\n", sym, q.RegularMarketPrice, q.RegularMarketOpen)
		}
	}

	return bot.sendMessage(msg, channel)
}

type CommandMessageHandler struct {
	prefix string

	commands map[string]Command
}

func NewCommandMessageHandler(prefix string) *CommandMessageHandler {
	return &CommandMessageHandler{
		prefix:   prefix,
		commands: make(map[string]Command),
	}
}

func (h *CommandMessageHandler) RegisterCommand(c Command) {
	h.commands[c.Name()] = c
}

func (h *CommandMessageHandler) OnEvent(ev slack.RTMEvent, bot *HBot) {
	e, ok := ev.Data.(*slack.MessageEvent)
	if !ok {
		return
	}

	if !strings.HasPrefix(e.Text, h.prefix) {
		return
	}

	log.Println(e.Text)

	args := strings.Split(e.Text[len(h.prefix):], " ")

	if len(args) == 0 {
		log.Printf("args 0 length: %v", args)
		return
	}

	cmd := args[0]
	args = args[1:]
	if c, ok := h.commands[cmd]; ok {
		err := c.OnMessage(cmd, args, e.User, e.Channel, bot)
		if err != nil {
			log.Println(err.Error())
		}
	}
}

type HBot struct {
	api *slack.Client

	handlers []Handler

	iconURL string
	botName string
}

func NewHBot(api *slack.Client, name, icon string) *HBot {
	return &HBot{
		api:     api,
		iconURL: icon,
		botName: name,
	}
}

func (b *HBot) sendMessage(text, channel string, attachments ...slack.Attachment) error {
	_, _, err := b.api.PostMessage(channel,
		slack.MsgOptionText(text, false),
		slack.MsgOptionUsername(b.botName),
		slack.MsgOptionAttachments(attachments...),
		slack.MsgOptionIconURL(b.iconURL),
	)
	if err != nil {
		log.Println(err.Error())
	}
	return err
}

func (b *HBot) RegisterHandler(h Handler) {
	b.handlers = append(b.handlers, h)
}

func (b *HBot) Start() error {
	rtm := b.api.NewRTM()
	go rtm.ManageConnection()

	for msg := range rtm.IncomingEvents {
		log.Printf("%+v", msg)
		switch ev := msg.Data.(type) {
		case *slack.InvalidAuthEvent:
			log.Printf("%+v", ev)
			return nil
		case *slack.RTMError:
			log.Printf("%+v", ev)
			return nil
		default:
			for _, h := range b.handlers {
				h.OnEvent(msg, b)
			}
		}
	}

	return nil
}

func main() {
	rand.Seed(time.Now().Unix())

	api := slack.New(os.Getenv("SLACK_BOT_TOKEN"))

	b := NewHBot(api, "hbot", "http://i.imgur.com/gLeA41v.jpg")
	ch := NewCommandMessageHandler("!")

	ch.RegisterCommand(&BangCommand{})
	ch.RegisterCommand(NewHelpCommand(ch))
	ch.RegisterCommand(&StockCommand{})
	ch.RegisterCommand(&CoinCommand{})

	fedfile := flag.String("fedfile", "", "path to fedfile")
	flag.Parse()

	if *fedfile != "" {
		fc, err := NewFedCommand(*fedfile)
		if err != nil {
			log.Fatal(err.Error())
		}
		log.Printf("registering fedcommand with fedfile %s", *fedfile)
		ch.RegisterCommand(fc)
	}

	b.RegisterHandler(ch)
	log.Fatal(b.Start().Error())
}
