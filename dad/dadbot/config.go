package dad

import (
	"encoding/json"
	// "fmt"
	"io/ioutil"
	"os"

	// log "gopkg.in/inconshreveable/log15.v2"
)

// ReadConfig reads each config file and returns a struct of each
func (ib *IRCBot) ReadConfig(ircFileName, botFileName, mutedFileName string) {
	ib.readIrcConfiguration(ircFileName)
	ib.readBotConfiguration(botFileName)
	ib.readMutedList(mutedFileName)
}

func (ib *IRCBot) readIrcConfiguration(fileName string) {
	file, _ := os.Open(fileName)
	defer file.Close()
	decoder := json.NewDecoder(file)
	ib.IRCConfig = IRCConfiguration{}
	err := decoder.Decode(&ib.IRCConfig)
	checkErr(err)
}

func (ib *IRCBot) readBotConfiguration(fileName string) {
	file, _ := os.Open(fileName)
	defer file.Close()
	decoder := json.NewDecoder(file)
	ib.BotConfig = BotConfiguration{}
	err := decoder.Decode(&ib.BotConfig)
	checkErr(err)
}

func (ib *IRCBot) readMutedList(fileName string) {
	file, _ := os.Open(fileName)
	defer file.Close()
	decoder := json.NewDecoder(file)
	ib.Muted = MutedList{}
	err := decoder.Decode(&ib.Muted)
	checkErr(err)
}

// TODO update doc
// UpdateConfig dispatches a call to the appropriate update function
// based on which bot is being run (mom or dad), parsing the current
// config information and rewriting it to the appropriate config file.
func (ib *IRCBot) UpdateBotConfig() {
	jsonData, err := json.MarshalIndent(ib.BotConfig, "", "    ")
	checkErr(err)
	ioutil.WriteFile(ib.BotConfigFile, jsonData, 0644)
}
