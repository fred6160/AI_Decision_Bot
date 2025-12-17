"""
AI Decision Recommendation Telegram Bot
A dynamic bot that helps students make structured decisions using weighted scoring frameworks.
"""

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import json
from datetime import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    DECISION_TYPE,
    NUM_OPTIONS,
    OPTION_NAMES,
    NUM_CRITERIA,
    CRITERIA_NAMES,
    CRITERIA_WEIGHTS,
    OPTION_SCORES,
    CONFIRM_CONTINUE,
) = range(8)


class DecisionBot:
    def __init__(self):
        self.user_data = {}

    def validate_number(self, text, min_val=1, max_val=10):
        """Validate if input is a number within range"""
        try:
            num = int(text)
            if min_val <= num <= max_val:
                return True, num
            return False, f"Please enter a number between {min_val} and {max_val}"
        except ValueError:
            return False, "Please enter a valid number"

    def validate_weight(self, text):
        """Validate weight input (1-10 scale)"""
        return self.validate_number(text, 1, 10)

    def validate_score(self, text):
        """Validate score input (1-10 scale)"""
        return self.validate_number(text, 1, 10)

    def calculate_weighted_scores(self, user_id):
        """Calculate weighted scores for all options"""
        data = self.user_data[user_id]
        criteria = data["criteria"]
        options = data["options"]

        # Calculate total weight for normalization
        total_weight = sum(c["weight"] for c in criteria)

        results = []
        for option in options:
            weighted_sum = 0
            details = []

            for criterion in criteria:
                score = option["scores"].get(criterion["name"], 0)
                weighted_value = (score * criterion["weight"]) / total_weight * 10
                weighted_sum += weighted_value
                details.append(
                    {
                        "criterion": criterion["name"],
                        "score": score,
                        "weight": criterion["weight"],
                        "weighted_value": round(weighted_value, 2),
                    }
                )

            results.append(
                {
                    "option": option["name"],
                    "total_score": round(weighted_sum, 2),
                    "details": details,
                }
            )

        # Sort by score (highest first)
        results.sort(key=lambda x: x["total_score"], reverse=True)
        return results

    def generate_recommendation(self, user_id):
        """Generate detailed recommendation text"""
        results = self.calculate_weighted_scores(user_id)
        data = self.user_data[user_id]

        recommendation = f"🎯 **DECISION ANALYSIS COMPLETE**\n\n"
        recommendation += f"📋 Decision: {data['decision_type']}\n"
        recommendation += f"📊 Options Analyzed: {len(data['options'])}\n"
        recommendation += f"⚖️ Criteria Used: {len(data['criteria'])}\n\n"

        recommendation += "═" * 40 + "\n\n"

        # Ranking
        recommendation += "🏆 **RANKING**\n\n"
        for i, result in enumerate(results, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            recommendation += f"{medal} **{result['option']}** - Score: {result['total_score']}/10\n"

        recommendation += "\n" + "═" * 40 + "\n\n"

        # Best option analysis
        best = results[0]
        recommendation += f"✅ **RECOMMENDATION: {best['option']}**\n\n"
        recommendation += "**Why this is the best choice:**\n\n"

        # Show breakdown
        for detail in best["details"]:
            recommendation += (
                f"• {detail['criterion']}: "
                f"{detail['score']}/10 (weight: {detail['weight']}/10) "
                f"= {detail['weighted_value']} points\n"
            )

        # Comparative analysis
        if len(results) > 1:
            recommendation += f"\n**Comparison with other options:**\n\n"
            second = results[1]
            diff = best["total_score"] - second["total_score"]
            recommendation += (
                f"• {best['option']} scores {diff:.2f} points higher than {second['option']}\n"
            )

            # Find strongest criteria
            strongest_criteria = max(best["details"], key=lambda x: x["weighted_value"])
            recommendation += (
                f"• Your strongest factor is '{strongest_criteria['criterion']}', "
                f"where {best['option']} excels\n"
            )

        # Key insights
        recommendation += "\n" + "═" * 40 + "\n\n"
        recommendation += "💡 **KEY INSIGHTS**\n\n"

        # Find user's priorities
        top_priority = max(data["criteria"], key=lambda x: x["weight"])
        recommendation += f"• Your top priority is '{top_priority['name']}' (weight: {top_priority['weight']}/10)\n"

        # Check if there's a close second
        if len(results) > 1:
            if results[1]["total_score"] >= results[0]["total_score"] * 0.9:
                recommendation += (
                    f"• ⚠️ Note: {results[1]['option']} is a very close second choice. "
                    f"Consider if there are other factors not captured here.\n"
                )

        recommendation += "\n" + "═" * 40 + "\n\n"
        recommendation += "📈 **DETAILED BREAKDOWN**\n\n"

        # Show all options with details
        for result in results:
            recommendation += f"**{result['option']}** ({result['total_score']}/10):\n"
            for detail in result["details"]:
                recommendation += f"  • {detail['criterion']}: {detail['score']}/10\n"
            recommendation += "\n"

        recommendation += "═" * 40 + "\n\n"
        recommendation += (
            "💭 Remember: This analysis is based on the factors YOU chose and weighted. "
            "Trust your judgment, but also consider factors that might not be easily quantified "
            "(gut feeling, long-term passion, etc.)\n\n"
        )
        recommendation += "Use /start to make another decision!"

        return recommendation


# Initialize bot
bot = DecisionBot()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask for decision type"""
    user_id = update.effective_user.id
    bot.user_data[user_id] = {
        "started": datetime.now().isoformat(),
        "criteria": [],
        "options": [],
    }

    await update.message.reply_text(
        "👋 Welcome to the AI Decision Recommendation Bot!\n\n"
        "I help students make better decisions using structured analysis.\n\n"
        "Let's start! 🎯\n\n"
        "What decision are you trying to make?\n\n"
        "Examples:\n"
        "• Choosing a final year project topic\n"
        "• Selecting an internship\n"
        "• Deciding on a major/course\n"
        "• Choosing a university\n"
        "• Deciding between study vs work\n\n"
        "Please describe your decision:"
    )
    return DECISION_TYPE


async def decision_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store decision type and ask for number of options"""
    user_id = update.effective_user.id
    decision = update.message.text.strip()

    if len(decision) < 5:
        await update.message.reply_text(
            "🤔 That seems too brief. Please describe your decision in more detail.\n\n"
            "Example: 'Choosing between three final year project topics'"
        )
        return DECISION_TYPE

    bot.user_data[user_id]["decision_type"] = decision

    await update.message.reply_text(
        f"Great! You're deciding: {decision}\n\n"
        f"📝 How many options are you comparing?\n\n"
        f"Please enter a number between 2 and 10:"
    )
    return NUM_OPTIONS


async def num_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store number of options and start collecting option names"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    valid, result = bot.validate_number(text, 2, 10)

    if not valid:
        await update.message.reply_text(
            f"❌ {result}\n\n"
            f"You need at least 2 options to compare, and maximum 10 options.\n\n"
            f"How many options do you have?"
        )
        return NUM_OPTIONS

    bot.user_data[user_id]["num_options"] = result
    bot.user_data[user_id]["current_option"] = 1

    await update.message.reply_text(
        f"Perfect! You're comparing {result} options.\n\n"
        f"📌 Now, let's name them.\n\n"
        f"Enter the name of Option 1:\n\n"
        f"Example: 'AI + Healthcare Project' or 'Google Internship'"
    )
    return OPTION_NAMES


async def option_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect all option names"""
    user_id = update.effective_user.id
    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text(
            "❌ Option name is too short. Please provide a meaningful name.\n\n"
            "Try again:"
        )
        return OPTION_NAMES

    current = bot.user_data[user_id]["current_option"]
    bot.user_data[user_id]["options"].append({"name": name, "scores": {}})

    if current < bot.user_data[user_id]["num_options"]:
        bot.user_data[user_id]["current_option"] += 1
        await update.message.reply_text(
            f"✅ Saved: {name}\n\n" f"Enter the name of Option {current + 1}:"
        )
        return OPTION_NAMES
    else:
        # All options collected
        option_list = "\n".join(
            [f"{i+1}. {opt['name']}" for i, opt in enumerate(bot.user_data[user_id]["options"])]
        )

        await update.message.reply_text(
            f"✅ All options saved!\n\n"
            f"Your options:\n{option_list}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Now let's define the CRITERIA you'll use to evaluate these options.\n\n"
            f"📊 How many criteria do you want to use?\n\n"
            f"Examples of criteria:\n"
            f"• Difficulty level\n"
            f"• Career relevance\n"
            f"• Time to complete\n"
            f"• Learning value\n"
            f"• Cost\n"
            f"• Supervisor availability\n\n"
            f"Enter a number between 2 and 10:"
        )
        return NUM_CRITERIA


async def num_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store number of criteria and start collecting criterion names"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    valid, result = bot.validate_number(text, 2, 10)

    if not valid:
        await update.message.reply_text(
            f"❌ {result}\n\n"
            f"You need at least 2 criteria, and maximum 10 criteria.\n\n"
            f"How many criteria do you want to use?"
        )
        return NUM_CRITERIA

    bot.user_data[user_id]["num_criteria"] = result
    bot.user_data[user_id]["current_criterion"] = 1

    await update.message.reply_text(
        f"Great! You'll use {result} criteria.\n\n"
        f"📋 Enter Criterion 1:\n\n"
        f"Example: 'Career Relevance' or 'Difficulty Level'"
    )
    return CRITERIA_NAMES


async def criteria_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect all criteria names"""
    user_id = update.effective_user.id
    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text(
            "❌ Criterion name is too short. Please provide a meaningful name.\n\n"
            "Try again:"
        )
        return CRITERIA_NAMES

    current = bot.user_data[user_id]["current_criterion"]
    bot.user_data[user_id]["criteria"].append({"name": name, "weight": 0})

    if current < bot.user_data[user_id]["num_criteria"]:
        bot.user_data[user_id]["current_criterion"] += 1
        await update.message.reply_text(f"✅ Saved: {name}\n\n" f"Enter Criterion {current + 1}:")
        return CRITERIA_NAMES
    else:
        # All criteria collected, now get weights
        criteria_list = "\n".join(
            [f"{i+1}. {crit['name']}" for i, crit in enumerate(bot.user_data[user_id]["criteria"])]
        )

        bot.user_data[user_id]["current_weight_index"] = 0

        first_criterion = bot.user_data[user_id]["criteria"][0]["name"]

        await update.message.reply_text(
            f"✅ All criteria saved!\n\n"
            f"Your criteria:\n{criteria_list}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚖️ Now, let's assign IMPORTANCE (weight) to each criterion.\n\n"
            f"Use a scale of 1-10:\n"
            f"• 1 = Not important at all\n"
            f"• 5 = Moderately important\n"
            f"• 10 = Extremely important\n\n"
            f"How important is '{first_criterion}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return CRITERIA_WEIGHTS


async def criteria_weights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect weights for each criterion"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    valid, weight = bot.validate_weight(text)

    if not valid:
        current_idx = bot.user_data[user_id]["current_weight_index"]
        criterion_name = bot.user_data[user_id]["criteria"][current_idx]["name"]
        await update.message.reply_text(
            f"❌ {weight}\n\n" f"How important is '{criterion_name}'?\n" f"Enter a number from 1 to 10:"
        )
        return CRITERIA_WEIGHTS

    current_idx = bot.user_data[user_id]["current_weight_index"]
    bot.user_data[user_id]["criteria"][current_idx]["weight"] = weight

    if current_idx + 1 < len(bot.user_data[user_id]["criteria"]):
        bot.user_data[user_id]["current_weight_index"] += 1
        next_criterion = bot.user_data[user_id]["criteria"][current_idx + 1]["name"]
        await update.message.reply_text(
            f"✅ Weight saved!\n\n" f"How important is '{next_criterion}'?\n" f"Enter a number from 1 to 10:"
        )
        return CRITERIA_WEIGHTS
    else:
        # All weights collected, now score options
        weights_summary = "\n".join(
            [
                f"• {crit['name']}: {crit['weight']}/10"
                for crit in bot.user_data[user_id]["criteria"]
            ]
        )

        bot.user_data[user_id]["current_score_option"] = 0
        bot.user_data[user_id]["current_score_criterion"] = 0

        first_option = bot.user_data[user_id]["options"][0]["name"]
        first_criterion = bot.user_data[user_id]["criteria"][0]["name"]

        await update.message.reply_text(
            f"✅ All weights saved!\n\n"
            f"Summary of your priorities:\n{weights_summary}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Now, let's SCORE each option against each criterion.\n\n"
            f"Use a scale of 1-10:\n"
            f"• 1 = Very poor on this criterion\n"
            f"• 5 = Average\n"
            f"• 10 = Excellent on this criterion\n\n"
            f"For '{first_option}',\n"
            f"How would you rate '{first_criterion}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return OPTION_SCORES


async def option_scores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect scores for each option-criterion combination"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    valid, score = bot.validate_score(text)

    if not valid:
        opt_idx = bot.user_data[user_id]["current_score_option"]
        crit_idx = bot.user_data[user_id]["current_score_criterion"]
        option_name = bot.user_data[user_id]["options"][opt_idx]["name"]
        criterion_name = bot.user_data[user_id]["criteria"][crit_idx]["name"]

        await update.message.reply_text(
            f"❌ {score}\n\n"
            f"For '{option_name}',\n"
            f"How would you rate '{criterion_name}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return OPTION_SCORES

    # Save score
    opt_idx = bot.user_data[user_id]["current_score_option"]
    crit_idx = bot.user_data[user_id]["current_score_criterion"]
    criterion_name = bot.user_data[user_id]["criteria"][crit_idx]["name"]
    bot.user_data[user_id]["options"][opt_idx]["scores"][criterion_name] = score

    # Move to next criterion or option
    num_criteria = len(bot.user_data[user_id]["criteria"])
    num_options = len(bot.user_data[user_id]["options"])

    if crit_idx + 1 < num_criteria:
        # More criteria for this option
        bot.user_data[user_id]["current_score_criterion"] += 1
        option_name = bot.user_data[user_id]["options"][opt_idx]["name"]
        next_criterion = bot.user_data[user_id]["criteria"][crit_idx + 1]["name"]

        await update.message.reply_text(
            f"✅ Score saved!\n\n"
            f"For '{option_name}',\n"
            f"How would you rate '{next_criterion}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return OPTION_SCORES
    elif opt_idx + 1 < num_options:
        # Move to next option
        bot.user_data[user_id]["current_score_option"] += 1
        bot.user_data[user_id]["current_score_criterion"] = 0
        next_option = bot.user_data[user_id]["options"][opt_idx + 1]["name"]
        first_criterion = bot.user_data[user_id]["criteria"][0]["name"]

        await update.message.reply_text(
            f"✅ All scores saved for this option!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"For '{next_option}',\n"
            f"How would you rate '{first_criterion}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return OPTION_SCORES
    else:
        # All scores collected - generate recommendation
        await update.message.reply_text(
            "✅ All data collected!\n\n"
            "🔄 Analyzing your decision...\n\n"
            "Please wait a moment..."
        )

        recommendation = bot.generate_recommendation(user_id)

        # Send recommendation in chunks if too long
        if len(recommendation) > 4096:
            for i in range(0, len(recommendation), 4096):
                await update.message.reply_text(recommendation[i : i + 4096])
        else:
            await update.message.reply_text(recommendation)

        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation"""
    await update.message.reply_text(
        "Decision analysis cancelled. Use /start to begin a new analysis.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restart the conversation"""
    user_id = update.effective_user.id
    if user_id in bot.user_data:
        del bot.user_data[user_id]
    
    await update.message.reply_text(
        "🔄 Restarting analysis...\n\n",
        reply_markup=ReplyKeyboardRemove(),
    )
    return await start(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message"""
    help_text = (
        "🤖 **AI Decision Recommendation Bot**\n\n"
        "This bot helps you make better decisions using weighted scoring analysis.\n\n"
        "**How it works:**\n"
        "1. Describe your decision\n"
        "2. List your options\n"
        "3. Define evaluation criteria\n"
        "4. Weight each criterion by importance\n"
        "5. Score each option on each criterion\n"
        "6. Get a detailed recommendation\n\n"
        "**Commands:**\n"
        "/start - Start a new decision analysis\n"
        "/restart - Restart the current analysis\n"
        "/help - Show this help message\n"
        "/cancel - Cancel current analysis\n\n"
        "**Tips:**\n"
        "• Be honest with your scoring\n"
        "• Consider both short and long-term factors\n"
        "• The bot can't capture everything (like gut feeling)\n"
        "• Use results as guidance, not absolute truth"
    )
    await update.message.reply_text(help_text)


def main() -> None:
    """Run the bot"""
    # Get token from environment variable
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TOKEN:
        print("ERROR: Please set TELEGRAM_BOT_TOKEN environment variable")
        print("Get your token from @BotFather on Telegram")
        return

    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DECISION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, decision_type)],
            NUM_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, num_options)],
            OPTION_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, option_names)],
            NUM_CRITERIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, num_criteria)],
            CRITERIA_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, criteria_names)],
            CRITERIA_WEIGHTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, criteria_weights)],
            OPTION_SCORES: [MessageHandler(filters.TEXT & ~filters.COMMAND, option_scores)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("restart", restart),
        ],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    # Run the bot
    print("Bot is starting...")
    print("Press Ctrl+C to stop")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()