# AI Decision Recommendation Telegram Bot - ENHANCED VERSION

> A fully dynamic, intelligent Telegram bot that helps students make structured, rational decisions using weighted scoring frameworks.

## 🎯 Project Goal

Build an AI-powered decision aid for students making critical academic and career choices (course selection, project topics, internships, university selection, etc.) using explainable, multi-criteria decision analysis.

---

## ✨ Key Features

### 1. **Intelligent Decision Validation** ✅
- Semantic validation ensures inputs are real student decisions
- Rejects spam, jokes, and off-topic requests
- Checks for decision keywords + domain relevance
- Clear error messages guide users to valid inputs

### 2. **Comprehensive Option & Criteria Management** ✅
- Support 2-10 options and 2-10 criteria (configurable)
- Duplicate detection for both options and criteria
- Meaningful name validation (min 3 chars, no numbers-only)
- Real-time progress tracking

### 3. **Weighted Scoring Framework** ✅
- 1-10 scale for criterion weights and option scores
- Clear guidance on what each scale level means
- Equal weight detection with user confirmation option
- Transparent weight summary display

### 4. **Edge Case Handling** ✅
- **Tied Scores**: Detects when top options have identical scores
  - Explains why they're tied
  - Provides actionable suggestions to break the tie
  - Never recommends randomly
  
- **Equal Weights**: Detects when all criteria have same importance
  - Warns user that priorities aren't differentiated
  - Offers choice to adjust or continue
  
- **Close Competition**: Alerts when 2nd place is within 7% of 1st
  - Suggests considering non-quantifiable factors

### 5. **Explainable Recommendations** ✅
- Shows EXACTLY why an option is recommended
- References top-weighted criteria
- Compares options against each other
- Provides transparent score breakdown
- Includes key insights and observations
- Respects user autonomy (decision aid, not replacement)

### 6. **Robust State Management** ✅
- Tracks conversation progress across 8 states
- Session data isolation per user
- Graceful error handling
- `/restart` clears session and starts fresh
- `/cancel` terminates analysis safely

---

## 📋 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Telegram account (for testing)

### Step 1: Clone/Download the Repository
```bash
git clone https://github.com/fred6160/AI_Decision_Bot.git
cd AI_Decision_Bot
```

### Step 2: Create Environment File
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your bot token
# Use a text editor to open .env and replace:
# TELEGRAM_BOT_TOKEN=your_bot_token_here_xxx:AAExxxxxxxxx
```

### Step 3: Get Your Telegram Bot Token
1. Open Telegram and search for `@BotFather`
2. Send `/start`
3. Send `/newbot` and follow the prompts
4. Copy the token provided and paste it in `.env`

Example token format:
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklmnoPQRstuvWXYZ
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Run the Bot
```bash
python AI_bot_enhanced.py
```

Expected output:
```
✅ Bot is starting...
📱 Press Ctrl+C to stop
```

### Step 6: Test the Bot
1. Open Telegram
2. Search for your bot by the name you gave it
3. Send `/start` to begin

---

## 🚀 Usage Guide

### Starting a Decision Analysis
```
/start
```
Bot will ask you to describe your decision.

### Commands
- `/start` - Start a new decision analysis
- `/restart` - Restart the current analysis (clears session)
- `/cancel` - Cancel and exit analysis
- `/help` - Show help and usage information

### Typical Workflow

**Step 1: Decision Description**
- Provide your decision in detail (min 15 chars)
- Example: "Choosing between three final year project topics in AI"

**Step 2: Number of Options**
- Enter count (2-10)
- Example: `3`

**Step 3: Option Names**
- Enter each option name (min 3 chars)
- Example: `AI in Healthcare`, `Blockchain Security`, `NLP Applications`

**Step 4: Number of Criteria**
- Enter count (2-10)
- Example: `4`

**Step 5: Criterion Names**
- Enter each criterion (min 3 chars)
- Example: `Career Relevance`, `Technical Difficulty`, `Time Required`, `Learning Value`

**Step 6: Criterion Weights**
- Assign importance to each criterion (1-10)
- 1-3: Low importance, 4-6: Moderate, 7-9: High, 10: Critical
- Example: `9`, `7`, `5`, `8`

**Step 7: Score Options**
- Rate each option against each criterion (1-10)
- 1-3: Poor, 4-6: Average, 7-9: Good, 10: Excellent
- Example: `9`, `7`, `6`, `9`

**Step 8: Recommendation**
- Bot calculates and displays comprehensive analysis
- Shows ranking, detailed breakdown, insights
- Provides actionable next steps

---

## 📊 Recommendation Output

The bot provides:

### 🏆 Ranking
Clear scoring of all options from best to worst

### ✅ Primary Recommendation
- Explains why this option is best
- References your top-weighted criteria
- Shows performance on each criterion

### 📈 Comparative Analysis
- Score difference from second place
- Decisive factors explaining the win
- Close competition warnings

### 💡 Key Insights
- Your highest priority
- Equal weight warnings
- Score variance analysis
- Tie detection with suggestions

### 📋 Detailed Breakdown
- Full score for each option on each criterion
- Weighted contribution to final score
- Transparent calculation reference

---

## 🛠 Architecture

### Core Classes

#### `DecisionValidator`
Semantic validation of user inputs
- `validate_decision_type()` - Validates real decisions
- `validate_option_name()` - Checks option names
- `validate_criterion_name()` - Checks criterion names

#### `DecisionBot`
Main decision analysis logic
- `validate_number()` - Numeric input validation
- `calculate_weighted_scores()` - Scoring algorithm
- `generate_recommendation()` - Report generation
- `check_equal_weights()` - Edge case detection
- `check_tied_scores()` - Tie detection

### Conversation States
```
DECISION_TYPE → NUM_OPTIONS → OPTION_NAMES → NUM_CRITERIA 
→ CRITERIA_NAMES → CRITERIA_WEIGHTS → WEIGHT_CONFIRMATION 
→ OPTION_SCORES → RECOMMENDATION
```

---

## 🔒 Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN` - Your bot's token from @BotFather

Optional:
- `LOG_LEVEL` - Logging verbosity (default: INFO)
- `POLLING_TIMEOUT` - Polling timeout in seconds (default: 30)
- `ALLOWED_USER_IDS` - Restrict bot to specific users (optional)

See `.env.example` for template.

---

## 📦 Dependencies

```
python-telegram-bot==22.5    # Telegram Bot API wrapper
python-dotenv==1.0.0         # Environment variable management
```

---

## 🧪 Testing

### Local Testing
```bash
# Set token in environment
export TELEGRAM_BOT_TOKEN="your_token_here"  # Linux/Mac
# or on Windows PowerShell:
$env:TELEGRAM_BOT_TOKEN="your_token_here"

# Run bot
python AI_bot_enhanced.py
```

### Test Scenarios

1. **Invalid Decision Input**
   - Input: `hello`, `123`, `abc`
   - Expected: Rejection with guidance

2. **Edge Case: Equal Weights**
   - Set all criteria weights to same value
   - Bot should warn and offer to continue/restart

3. **Edge Case: Tied Scores**
   - Design options with identical total scores
   - Bot should explain tie and suggest refinements

4. **Close Competition**
   - Rank options with 5-7% score difference
   - Bot should warn user to consider non-quantifiable factors

---

## 🚀 Deployment

### Option 1: Heroku (Recommended for Free Hosting)
```bash
# Install Heroku CLI, then:
heroku login
heroku create your-bot-name
heroku config:set TELEGRAM_BOT_TOKEN="your_token"
git push heroku main
```

### Option 2: Docker
```bash
# Build
docker build -t decision-bot .

# Run
docker run -e TELEGRAM_BOT_TOKEN="your_token" decision-bot
```

### Option 3: VPS/Server
```bash
# Clone repo, install deps, run with systemd/supervisor
sudo systemctl start decision-bot
```

---

## 📝 Example Conversation

```
User: /start
Bot: 👋 Welcome to the AI Decision Recommendation Bot!...

User: Choosing between three internship offers
Bot: ✅ Great! Your decision: "Choosing between three internship offers"
     📝 How many options are you comparing?

User: 3
Bot: Perfect! You're comparing 3 options.
     📌 Let's name them.
     Enter the name of Option 1:

User: Google Software Engineer
Bot: ✅ Saved: Google Software Engineer
     Enter the name of Option 2:

User: Microsoft Cloud Architect
Bot: ✅ Saved: Microsoft Cloud Architect
     Enter the name of Option 3:

User: Startup AI Engineer
Bot: ✅ All options saved!
     📊 How many criteria do you want to use?

User: 4
Bot: 📋 Enter Criterion 1:

User: Salary & Compensation
Bot: ✅ Saved: Salary & Compensation
     Enter Criterion 2:

User: Career Growth
Bot: ✅ Saved: Career Growth
     Enter Criterion 3:

User: Work-Life Balance
Bot: ✅ Saved: Work-Life Balance
     Enter Criterion 4:

User: Learning Opportunity
Bot: ✅ All criteria saved!
     ⚖️ How important is 'Salary & Compensation'? (1-10)

User: 8
Bot: How important is 'Career Growth'? (1-10)

User: 9
Bot: How important is 'Work-Life Balance'? (1-10)

User: 7
Bot: How important is 'Learning Opportunity'? (1-10)

User: 8
Bot: ✅ All weights saved!
     📊 For 'Google Software Engineer', how would you rate 'Salary & Compensation'? (1-10)

User: 9
[... scoring continues ...]

Bot: ✅ All data collected!
     🎯 DECISION ANALYSIS COMPLETE
     
     📋 Your Decision: Choosing between three internship offers
     📊 Options Analyzed: 3
     ⚖️ Criteria Used: 4
     
     🏆 RANKING
     🥇 Microsoft Cloud Architect → 8.45/10
     🥈 Google Software Engineer → 8.20/10
     🥉 Startup AI Engineer → 7.65/10
     
     ✅ RECOMMENDATION: Microsoft Cloud Architect
     
     📊 WHY THIS IS THE BEST CHOICE:
     
     Based on your priorities, Microsoft Cloud Architect excels in:
     
     1. Career Growth (your priority weight: 9/10 - Your priority)
        Microsoft Cloud Architect scored: 9/10 - 🟢 Excellent
        Contributes 2.12 points to the final score
     ...
```

---

## 🐛 Troubleshooting

### "ERROR: TELEGRAM_BOT_TOKEN environment variable is not set"
**Solution:** 
- Create `.env` file with `TELEGRAM_BOT_TOKEN=your_token`
- Or: `export TELEGRAM_BOT_TOKEN="your_token"`

### Bot doesn't respond to messages
**Solution:**
- Check bot token is correct
- Verify bot has been started with `/start`
- Check internet connection
- Look at log output for errors

### "python-telegram-bot" not found
**Solution:**
```bash
pip install -r requirements.txt
```

### Recommendation shows zero scores
**Solution:**
- Ensure you entered valid scores (1-10) for all options
- Check that all criteria have non-zero weights

---

## 📚 Advanced Features (Roadmap)

- ✅ Decision validation with semantic checking
- ✅ Edge case handling (ties, equal weights)
- ✅ Explainable recommendations
- 🔄 Persistent storage (database support)
- 🔄 User profiles and history
- 🔄 Analytics dashboard
- 🔄 Multi-language support
- 🔄 Export recommendations as PDF

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👤 Author

**Fred** - [GitHub: fred6160](https://github.com/fred6160)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

Feel free to:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

## ⭐ If You Find This Useful

Please give this repository a ⭐ on GitHub to help others discover it!

---

**Last Updated:** December 19, 2025
**Version:** 2.0 (Enhanced)
**Status:** Production Ready ✅
