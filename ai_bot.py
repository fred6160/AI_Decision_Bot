"""
AI Decision Recommendation Telegram Bot - ENHANCED VERSION
A fully dynamic, intelligent bot for structured student decision-making.

This bot helps students make rational, structured decisions using weighted scoring frameworks.
It validates inputs, handles edge cases, and provides explainable recommendations.

Deployment: Use TELEGRAM_BOT_TOKEN environment variable or .env file
"""

import os
import logging
import re
from typing import Tuple, Optional, List, Dict
from datetime import datetime

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Load environment variables from .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env support is optional

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
    WEIGHT_CONFIRMATION,
    OPTION_SCORES,
) = range(8)


class DecisionValidator:
    """Handles semantic validation of user inputs with intelligent pattern matching"""

    # Valid decision domains (student context)
    VALID_DOMAINS = {
        "course": ["course", "major", "degree", "program", "subject", "module", "class"],
        "academic": ["project", "thesis", "dissertation", "research", "topic", "paper"],
        "career": ["job", "internship", "position", "company", "role", "career", "work"],
        "university": ["university", "college", "postgraduate", "masters", "phd", "scholarship"],
        "choice": ["choosing", "selecting", "deciding", "between", "which", "should", "pick"],
    }

    INVALID_KEYWORDS = [
        "joke", "test", "hello", "hi", "what", "weather", "recipe", "movie",
        "game", "sports", "music", "date", "relationship", "friend"
    ]

    @staticmethod
    def validate_decision_type(text: str) -> Tuple[bool, Optional[str]]:
        """
        Intelligently validate if input is a real student decision.
        Checks: length, keywords, sentence structure, and domain relevance.
        
        Returns: (is_valid, error_message or None)
        """
        text_lower = text.lower().strip()

        # Check 1: Minimum meaningful length
        if len(text.strip()) < 15:
            return False, (
                "❌ That's too brief to be a real decision.\n\n"
                "Please provide at least 15 characters describing your decision.\n\n"
                "Example: 'Should I choose Computer Science or Data Science?'"
            )

        # Check 2: Reject obvious non-decisions
        for invalid in DecisionValidator.INVALID_KEYWORDS:
            if text_lower.startswith(invalid):
                return False, (
                    "❌ That doesn't appear to be an academic or career decision.\n\n"
                    "This bot helps with:\n"
                    "✅ Choosing courses or majors\n"
                    "✅ Selecting project topics\n"
                    "✅ Deciding between internships or jobs\n"
                    "✅ University or postgraduate choices\n"
                    "✅ Study vs work decisions\n\n"
                    "Please describe a real student decision."
                )

        # Check 3: Must contain decision words + domain keywords
        has_decision_indicator = any(
            keyword in text_lower 
            for keyword in DecisionValidator.VALID_DOMAINS["choice"]
        )

        has_domain = any(
            keyword in text_lower 
            for domain_keywords in DecisionValidator.VALID_DOMAINS.values()
            for keyword in domain_keywords
        )

        if not (has_decision_indicator or has_domain):
            return False, (
                "❌ I can't identify a clear academic or career decision here.\n\n"
                "Your decision should mention:\n"
                "• A choice (e.g., 'choosing between', 'should I', 'which is better')\n"
                "• A student-related context (course, project, job, university, etc.)\n\n"
                "Example: 'Choosing between three final year project topics in AI'"
            )

        # Check 4: Reject spam patterns (single letters repeated, numbers only, etc.)
        if re.match(r"^[a-z0-9\s]{1,3}$", text_lower):
            return False, (
                "❌ That looks like spam or test input.\n\n"
                "Please describe a real decision."
            )

        # All checks passed
        return True, None

    @staticmethod
    def is_gibberish(text: str) -> bool:
        """
        Detect if text is gibberish/rubbish input.
        Checks for random letter sequences, no vowels, etc.
        More lenient - allows real words and company names.
        """
        text_lower = text.lower().strip()
        
        # Allow if contains spaces (indicates multi-word, likely valid)
        if ' ' in text_lower:
            return False
        
        # Check 1: NO vowels at all AND length > 3 = likely gibberish
        vowels = "aeiou"
        vowel_count = sum(1 for char in text_lower if char in vowels)
        alpha_only = ''.join(c for c in text_lower if c.isalpha())
        
        if len(alpha_only) > 3 and vowel_count == 0:
            return True  # "kfhkjfk" has no vowels
        
        # Check 2: ONLY consecutive repeated characters (not scattered)
        # Example: "kkkkk" or "ffff" = gibberish
        # But "Google" (oo in middle) is fine
        if re.search(r'([a-z])\1{3,}', text_lower):  # 4+ same char in a row
            return True
        
        # Check 3: Very short gibberish pattern (2-3 chars, random)
        if len(text_lower) == 2 and vowel_count == 0:
            return True
        
        # Check 4: Random keyboard mashing (lots of consonants scattered)
        # Only flag if VERY few vowels relative to length
        if len(alpha_only) >= 6:  # Only check longer inputs
            vowel_ratio = vowel_count / len(alpha_only)
            if vowel_ratio < 0.15:  # Less than 15% vowels in 6+ letter word = suspicious
                return True
        
        return False

    @staticmethod
    def validate_option_name(name: str, existing_options: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate an option name for uniqueness and meaningfulness"""
        name = name.strip()

        if len(name) < 3:
            return False, (
                "❌ Option name is too short.\n"
                "Please provide a meaningful name (at least 3 characters)."
            )

        # Check for exact duplicates (case-insensitive)
        existing_lower = [opt.lower() for opt in existing_options]
        if name.lower() in existing_lower:
            return False, f"❌ You've already entered '{name}'. Please provide a different option."

        # Reject pure numbers or single characters
        if name.isdigit() or len(name) <= 1:
            return False, "❌ Please enter a descriptive name, not just numbers or symbols."

        # NEW: Detect gibberish/rubbish input
        if DecisionValidator.is_gibberish(name):
            return False, (
                "❌ That doesn't look like a real option name.\n\n"
                "Please provide a meaningful, descriptive option name.\n\n"
                "Examples (for internship decision):\n"
                "• Google Software Engineer\n"
                "• Microsoft Cloud Architect\n"
                "• Startup AI Engineer\n\n"
                "Try again:"
            )

        return True, None

    @staticmethod
    def validate_criterion_name(name: str, existing_criteria: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate a criterion name for uniqueness and meaningfulness"""
        name = name.strip()

        if len(name) < 3:
            return False, (
                "❌ Criterion name is too short.\n"
                "Please provide a meaningful criterion (at least 3 characters)."
            )

        # Check for duplicates (case-insensitive)
        existing_lower = [crit.lower() for crit in existing_criteria]
        if name.lower() in existing_lower:
            return False, f"❌ You've already entered '{name}'. Please provide a different criterion."

        return True, None


class DecisionBot:
    """Main bot logic with enhanced intelligence and edge-case handling"""

    def __init__(self):
        self.user_data = {}

    def validate_number(self, text: str, min_val: int = 1, max_val: int = 10) -> Tuple[bool, any]:
        """Validate if input is a number within range"""
        try:
            num = int(text.strip())
            if min_val <= num <= max_val:
                return True, num
            return False, f"Please enter a number between {min_val} and {max_val}"
        except ValueError:
            return False, "Please enter a valid number (digits only)"

    def check_equal_weights(self, user_id: int) -> bool:
        """Check if all criterion weights are equal"""
        if user_id not in self.user_data:
            return False
        weights = [c["weight"] for c in self.user_data[user_id].get("criteria", [])]
        return len(set(weights)) == 1 if weights else False

    def check_tied_scores(self, results: List[Dict]) -> bool:
        """Check if top options have identical scores"""
        if len(results) < 2:
            return False
        return results[0]["total_score"] == results[1]["total_score"]

    def get_tied_options(self, results: List[Dict]) -> List[str]:
        """Get list of options tied for first place"""
        if not results:
            return []
        top_score = results[0]["total_score"]
        return [r["option"] for r in results if r["total_score"] == top_score]

    def calculate_weighted_scores(self, user_id: int) -> List[Dict]:
        """Calculate weighted scores for all options with transparent computation"""
        if user_id not in self.user_data:
            return []

        data = self.user_data[user_id]
        criteria = data.get("criteria", [])
        options = data.get("options", [])

        # Protect against division by zero
        total_weight = sum(c["weight"] for c in criteria)
        if total_weight == 0:
            total_weight = 1

        results = []
        for option in options:
            weighted_sum = 0
            details = []

            for criterion in criteria:
                score = option["scores"].get(criterion["name"], 0)
                if total_weight > 0:
                    weighted_value = (score * criterion["weight"]) / total_weight * 10
                else:
                    weighted_value = 0

                weighted_sum += weighted_value
                details.append({
                    "criterion": criterion["name"],
                    "score": score,
                    "weight": criterion["weight"],
                    "weighted_value": round(weighted_value, 2),
                })

            results.append({
                "option": option["name"],
                "total_score": round(weighted_sum, 2),
                "details": details,
            })

        # Sort by score (highest first)
        results.sort(key=lambda x: x["total_score"], reverse=True)
        return results

    def generate_recommendation(self, user_id: int) -> str:
        """Generate detailed, explainable, non-generic recommendation"""
        if user_id not in self.user_data:
            return "Error: Session data not found. Please use /start."

        results = self.calculate_weighted_scores(user_id)
        data = self.user_data[user_id]

        if not results:
            return "Error: Unable to calculate scores. Please try again with /restart."

        # Start recommendation
        recommendation = "🎯 DECISION ANALYSIS COMPLETE\n\n"
        recommendation += f"📋 Your Decision: {data.get('decision_type', 'Unknown')}\n"
        recommendation += f"📊 Options Analyzed: {len(data.get('options', []))}\n"
        recommendation += f"⚖️  Criteria Used: {len(data.get('criteria', []))}\n\n"
        recommendation += "═" * 50 + "\n\n"

        # Check for tied scores
        is_tied = self.check_tied_scores(results)
        tied_options = self.get_tied_options(results) if is_tied else []

        # SECTION 1: Ranking
        recommendation += "🏆 RANKING (by final score)\n\n"
        for i, result in enumerate(results, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            recommendation += f"{medal} {result['option']} → {result['total_score']}/10\n"

        recommendation += "\n" + "═" * 50 + "\n\n"

        # SECTION 2: Handle Tied Results
        if is_tied:
            recommendation += "⚠️  TIE DETECTED!\n\n"
            recommendation += f"These options are tied with identical scores ({results[0]['total_score']}/10):\n"
            for opt in tied_options:
                recommendation += f"• {opt}\n"
            recommendation += "\n"
            recommendation += "This means they perform equally well based on your current criteria and weights.\n\n"
            recommendation += "💡 TO BREAK THE TIE, YOU CAN:\n"
            recommendation += "1. Add new criteria you may have overlooked (e.g., personal fulfillment, mentorship)\n"
            recommendation += "2. Re-score options more carefully\n"
            recommendation += "3. Adjust criterion weights to reflect true priorities\n"
            recommendation += "4. Trust non-quantifiable factors (gut feeling, passion, advisor input)\n\n"
            recommendation += "Try /restart to refine your analysis further.\n\n"
            recommendation += "═" * 50 + "\n\n"

        # SECTION 3: Best Option Analysis
        best = results[0]
        recommendation += f"✅ RECOMMENDATION: {best['option']}\n\n"

        # Explain why this option won
        recommendation += "📊 WHY THIS IS THE BEST CHOICE:\n\n"

        # Get top 3 weighted criteria
        data_criteria = data.get("criteria", [])
        top_criteria = sorted(data_criteria, key=lambda x: x["weight"], reverse=True)[:3]

        recommendation += f"Based on your priorities, {best['option']} excels in:\n\n"

        for rank, crit in enumerate(top_criteria, 1):
            matching_detail = next((d for d in best["details"] if d["criterion"] == crit["name"]), None)
            if matching_detail:
                score_level = "🔴 Poor" if matching_detail["score"] <= 3 else \
                             "🟡 Fair" if matching_detail["score"] <= 5 else \
                             "🟢 Strong" if matching_detail["score"] <= 8 else \
                             "🟢 Excellent"

                recommendation += (
                    f"{rank}. {crit['name']} (Your weight: {crit['weight']}/10 - Your priority)\n"
                    f"   {best['option']} scored: {matching_detail['score']}/10 {score_level}\n"
                    f"   Contributes {matching_detail['weighted_value']} points\n\n"
                )

        # SECTION 4: Comparative Analysis
        if len(results) > 1 and not is_tied:
            recommendation += "📈 COMPARISON WITH ALTERNATIVES:\n\n"
            second = results[1]
            diff = best["total_score"] - second["total_score"]
            recommendation += f"• {best['option']} outperforms {second['option']} by {diff:.2f} points\n\n"

            # Find key differentiators
            largest_gap = 0
            decisive_criterion = None
            for i, detail in enumerate(best["details"]):
                second_detail = second["details"][i]
                gap = detail["weighted_value"] - second_detail["weighted_value"]
                if gap > largest_gap:
                    largest_gap = gap
                    decisive_criterion = detail["criterion"]

            if decisive_criterion:
                recommendation += (
                    f"• The decisive factor: {decisive_criterion}\n"
                    f"  {best['option']} significantly outperforms alternatives here\n\n"
                )

            # Check for close competition
            score_ratio = second["total_score"] / best["total_score"] if best["total_score"] > 0 else 0
            if score_ratio >= 0.93:  # Within 7%
                recommendation += (
                    f"⚠️  CLOSE COMPETITION: {second['option']} is very close behind.\n"
                    f"Consider non-quantifiable factors before finalizing your choice.\n\n"
                )

        recommendation += "═" * 50 + "\n\n"

        # SECTION 5: Key Insights
        recommendation += "💡 KEY INSIGHTS & OBSERVATIONS\n\n"

        top_priority = max(data_criteria, key=lambda x: x["weight"]) if data_criteria else None
        if top_priority:
            recommendation += f"• Your highest priority is '{top_priority['name']}' (weight: {top_priority['weight']}/10)\n"

        # Check if weights were all equal
        if self.check_equal_weights(user_id):
            recommendation += (
                "• ⚠️  Note: All criteria have equal weight.\n"
                "  This means you treated all factors as equally important.\n"
                "  Consider if some factors should genuinely matter more.\n"
            )

        # Variance analysis
        scores = [r["total_score"] for r in results]
        if len(scores) > 1:
            max_score = max(scores)
            min_score = min(scores)
            variance = max_score - min_score
            if variance < 1:
                recommendation += (
                    f"• The scores are very close (variance: {variance:.2f}).\n"
                    f"  Options are nearly equivalent; personal preference matters more.\n"
                )

        recommendation += "\n" + "═" * 50 + "\n\n"

        # SECTION 6: Detailed Score Breakdown
        recommendation += "📋 DETAILED BREAKDOWN (all options & criteria)\n\n"
        for idx, result in enumerate(results, 1):
            recommendation += f"{idx}. {result['option']} (Total: {result['total_score']}/10)\n"
            for detail in result["details"]:
                recommendation += (
                    f"  • {detail['criterion']}: "
                    f"Score {detail['score']}/10 × Weight {detail['weight']}/10 = {detail['weighted_value']} pts\n"
                )
            recommendation += "\n"

        recommendation += "═" * 50 + "\n\n"

        # FINAL NOTES
        recommendation += (
            "💭 FINAL REMINDERS\n\n"
            "✓ This analysis is OBJECTIVE and DATA-DRIVEN based on your inputs.\n"
            "✓ However, not everything can be quantified (passion, mentorship, gut feeling).\n"
            "✓ This is a DECISION AID, not a replacement for your judgment.\n"
            "✓ Trust the analysis, but also trust yourself.\n\n"
            "Ready to analyze another decision? Use /start\n"
            "Want to refine this analysis? Use /restart\n"
        )

        return recommendation


# Initialize bot and validator
bot = DecisionBot()
validator = DecisionValidator()


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and initialize user session"""
    try:
        user_id = update.effective_user.id
        logger.info(f"Start command received from user {user_id}")

        # Initialize fresh user data
        bot.user_data[user_id] = {
            "started": datetime.now().isoformat(),
            "criteria": [],
            "options": [],
            "decision_type": None,
        }

        await update.message.reply_text(
            "👋 Welcome to the AI Decision Recommendation Bot!\n\n"
            "I help students make better decisions using structured, weighted analysis.\n\n"
            "✅ Perfect for:\n"
            "• Choosing a course or major\n"
            "• Selecting a final year project topic\n"
            "• Deciding between internships\n"
            "• Choosing a university or postgraduate program\n"
            "• Study vs work decisions\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 Let's begin! Please describe your decision in detail:\n\n"
            "Example: 'Choosing between three final year project topics in AI and machine learning'"
        )
        logger.info(f"Start message sent to user {user_id}, returning DECISION_TYPE state")
        return DECISION_TYPE
    except Exception as e:
        logger.error(f"Error in start handler: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred. Please try again with /start"
        )
        return ConversationHandler.END


async def decision_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate and store decision type with semantic checking"""
    user_id = update.effective_user.id
    decision = update.message.text.strip()

    # Validate decision
    is_valid, error_msg = validator.validate_decision_type(decision)

    if not is_valid:
        await update.message.reply_text(error_msg)
        return DECISION_TYPE

    # Store the validated decision
    bot.user_data[user_id]["decision_type"] = decision

    await update.message.reply_text(
        f"✅ Great! Your decision:\n\n\"{decision}\"\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 Step 1: How many options are you comparing?\n\n"
        f"Enter a number between 2 and 10:"
    )
    return NUM_OPTIONS


async def num_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate and store number of options"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    valid, result = bot.validate_number(text, 2, 10)

    if not valid:
        await update.message.reply_text(
            f"❌ {result}\n\n"
            f"You need at least 2 options to compare (maximum 10).\n\n"
            f"How many options do you have?"
        )
        return NUM_OPTIONS

    bot.user_data[user_id]["num_options"] = result
    bot.user_data[user_id]["current_option"] = 1

    await update.message.reply_text(
        f"Perfect! You're comparing {result} options.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 Step 2: Let's name them\n\n"
        f"Enter the name of Option 1:\n\n"
        f"Example: 'AI in Healthcare' or 'Google Software Internship'"
    )
    return OPTION_NAMES


async def option_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect and validate option names"""
    user_id = update.effective_user.id
    name = update.message.text.strip()

    # Get existing option names
    existing = [opt["name"] for opt in bot.user_data[user_id]["options"]]

    # Validate
    is_valid, error_msg = validator.validate_option_name(name, existing)

    if not is_valid:
        await update.message.reply_text(f"{error_msg}\n\nTry again:")
        return OPTION_NAMES

    current = bot.user_data[user_id]["current_option"]
    bot.user_data[user_id]["options"].append({"name": name, "scores": {}})

    if current < bot.user_data[user_id]["num_options"]:
        bot.user_data[user_id]["current_option"] += 1
        await update.message.reply_text(
            f"✅ Saved: {name}\n\n"
            f"Enter the name of Option {current + 1}:"
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
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Step 3: Define evaluation criteria\n\n"
            f"How many criteria do you want to use?\n\n"
            f"Common examples:\n"
            f"• Career relevance\n"
            f"• Difficulty/Complexity\n"
            f"• Time required\n"
            f"• Cost/Budget\n"
            f"• Learning value\n"
            f"• Future opportunities\n\n"
            f"Enter a number between 2 and 10:"
        )
        return NUM_CRITERIA


async def num_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate and store number of criteria"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    valid, result = bot.validate_number(text, 2, 10)

    if not valid:
        await update.message.reply_text(
            f"❌ {result}\n\n"
            f"You need at least 2 criteria (maximum 10).\n\n"
            f"How many criteria do you want?"
        )
        return NUM_CRITERIA

    bot.user_data[user_id]["num_criteria"] = result
    bot.user_data[user_id]["current_criterion"] = 1

    await update.message.reply_text(
        f"Great! You'll use {result} criteria.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 Enter Criterion 1:\n\n"
        f"Example: 'Career Relevance' or 'Project Difficulty'"
    )
    return CRITERIA_NAMES


async def criteria_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect and validate criteria names"""
    user_id = update.effective_user.id
    name = update.message.text.strip()

    # Get existing criteria names
    existing = [crit["name"] for crit in bot.user_data[user_id]["criteria"]]

    # Validate
    is_valid, error_msg = validator.validate_criterion_name(name, existing)

    if not is_valid:
        await update.message.reply_text(f"{error_msg}\n\nTry again:")
        return CRITERIA_NAMES

    current = bot.user_data[user_id]["current_criterion"]
    bot.user_data[user_id]["criteria"].append({"name": name, "weight": 0})

    if current < bot.user_data[user_id]["num_criteria"]:
        bot.user_data[user_id]["current_criterion"] += 1
        await update.message.reply_text(
            f"✅ Saved: {name}\n\n"
            f"Enter Criterion {current + 1}:"
        )
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
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚖️  Step 4: Assign IMPORTANCE (weight) to each criterion\n\n"
            f"Use a scale of 1-10:\n"
            f"• 1-3 = Low importance (nice to have)\n"
            f"• 4-6 = Moderate importance (matters)\n"
            f"• 7-9 = High importance (very important)\n"
            f"• 10 = Critical (absolutely essential)\n\n"
            f"How important is '{first_criterion}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return CRITERIA_WEIGHTS


async def criteria_weights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect weights for each criterion"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    valid, weight = bot.validate_number(text, 1, 10)

    if not valid:
        current_idx = bot.user_data[user_id]["current_weight_index"]
        criterion_name = bot.user_data[user_id]["criteria"][current_idx]["name"]
        await update.message.reply_text(
            f"❌ {weight}\n\n"
            f"How important is '{criterion_name}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return CRITERIA_WEIGHTS

    current_idx = bot.user_data[user_id]["current_weight_index"]
    bot.user_data[user_id]["criteria"][current_idx]["weight"] = weight

    if current_idx + 1 < len(bot.user_data[user_id]["criteria"]):
        bot.user_data[user_id]["current_weight_index"] += 1
        next_criterion = bot.user_data[user_id]["criteria"][current_idx + 1]["name"]
        await update.message.reply_text(
            f"✅ Weight saved!\n\n"
            f"How important is '{next_criterion}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return CRITERIA_WEIGHTS
    else:
        # All weights collected - show summary
        weights_summary = "\n".join(
            [f"• {crit['name']}: {crit['weight']}/10" for crit in bot.user_data[user_id]["criteria"]]
        )

        await update.message.reply_text(
            f"✅ All weights saved!\n\n"
            f"Your priorities:\n{weights_summary}\n\n"
        )

        # Check if all weights are equal
        if bot.check_equal_weights(user_id):
            await update.message.reply_text(
                "⚠️  NOTICE: All criteria have equal weight\n\n"
                "You've assigned the same importance to all factors.\n"
                "While valid, this might not reflect your true priorities.\n\n"
                "Do you want to:\n"
                "1️⃣  Continue anyway (reply: continue)\n"
                "2️⃣  Adjust weights (use: /restart)\n\n"
                "Reply with 'continue' or use /restart:"
            )
            return WEIGHT_CONFIRMATION
        else:
            # Proceed directly to scoring
            return await start_scoring(update, context)


async def weight_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's choice on equal weights"""
    user_id = update.effective_user.id
    response = update.message.text.strip().lower()

    if response == "continue":
        return await start_scoring(update, context)
    else:
        await update.message.reply_text(
            "Please reply 'continue' to proceed, or use /restart to adjust weights."
        )
        return WEIGHT_CONFIRMATION


async def start_scoring(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Begin the scoring phase"""
    user_id = update.effective_user.id

    bot.user_data[user_id]["current_score_option"] = 0
    bot.user_data[user_id]["current_score_criterion"] = 0

    first_option = bot.user_data[user_id]["options"][0]["name"]
    first_criterion = bot.user_data[user_id]["criteria"][0]["name"]

    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Step 5: SCORE each option against each criterion\n\n"
        f"Use a scale of 1-10:\n"
        f"• 1-3 = Poor/Weak performance\n"
        f"• 4-6 = Average/Moderate performance\n"
        f"• 7-9 = Good/Strong performance\n"
        f"• 10 = Excellent/Outstanding performance\n\n"
        f"For '{first_option}',\n"
        f"How would you rate '{first_criterion}'?\n\n"
        f"Enter a number from 1 to 10:"
    )
    return OPTION_SCORES


async def option_scores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect and validate scores for each option-criterion pair"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    valid, score = bot.validate_number(text, 1, 10)

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

    # Get current indices
    opt_idx = bot.user_data[user_id]["current_score_option"]
    crit_idx = bot.user_data[user_id]["current_score_criterion"]
    
    # Get option and criterion names BEFORE any state changes
    current_option_name = bot.user_data[user_id]["options"][opt_idx]["name"]
    criterion_name = bot.user_data[user_id]["criteria"][crit_idx]["name"]
    
    # Save score
    bot.user_data[user_id]["options"][opt_idx]["scores"][criterion_name] = score

    # Calculate progress
    num_criteria = len(bot.user_data[user_id]["criteria"])
    num_options = len(bot.user_data[user_id]["options"])
    total_scores = num_options * num_criteria
    current_score_number = (opt_idx * num_criteria) + crit_idx + 1
    progress_pct = int((current_score_number / total_scores) * 100)

    # Determine next state
    if crit_idx + 1 < num_criteria:
        # More criteria for this option - update state BEFORE sending message
        next_crit_idx = crit_idx + 1
        next_criterion_name = bot.user_data[user_id]["criteria"][next_crit_idx]["name"]
        
        # Update state
        bot.user_data[user_id]["current_score_criterion"] = next_crit_idx
        
        # Send message
        await update.message.reply_text(
            f"✅ Score saved! [{progress_pct}% complete]\n\n"
            f"For '{current_option_name}',\n"
            f"How would you rate '{next_criterion_name}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return OPTION_SCORES
        
    elif opt_idx + 1 < num_options:
        # More options - update state BEFORE sending message
        next_opt_idx = opt_idx + 1
        next_option_name = bot.user_data[user_id]["options"][next_opt_idx]["name"]
        first_criterion_name = bot.user_data[user_id]["criteria"][0]["name"]
        
        # Update state
        bot.user_data[user_id]["current_score_option"] = next_opt_idx
        bot.user_data[user_id]["current_score_criterion"] = 0
        
        # Send message with updated indices for proper progress calculation
        next_score_number = (next_opt_idx * num_criteria) + 0 + 1
        next_progress_pct = int((next_score_number / total_scores) * 100)
        
        await update.message.reply_text(
            f"✅ All scores saved for {current_option_name}! [{progress_pct}% complete]\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"For '{next_option_name}',\n"
            f"How would you rate '{first_criterion_name}'?\n"
            f"Enter a number from 1 to 10:"
        )
        return OPTION_SCORES
        
    else:
        # All scores collected - generate recommendation
        await update.message.reply_text(
            "✅ All data collected! [100% complete]\n\n"
            "🔄 Analyzing your decision...\n\n"
            "Please wait a moment..."
        )

        recommendation = bot.generate_recommendation(user_id)

        # Send recommendation in chunks if too long (Telegram 4096 char limit)
        if len(recommendation) > 4096:
            for i in range(0, len(recommendation), 4096):
                chunk = recommendation[i:i + 4096]
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(recommendation)

        return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restart the entire analysis from scratch"""
    user_id = update.effective_user.id
    if user_id in bot.user_data:
        del bot.user_data[user_id]

    await update.message.reply_text(
        "🔄 Restarting analysis...\n\n"
        "All previous data has been cleared.\n\n",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Restart the conversation
    return await start(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current analysis"""
    user_id = update.effective_user.id
    if user_id in bot.user_data:
        del bot.user_data[user_id]

    await update.message.reply_text(
        "❌ Analysis cancelled.\n\n"
        "Your session has been cleared.\n\n"
        "Use /start whenever you're ready to make a new decision analysis.\n"
        "Use /help for more information.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help and usage information"""
    help_text = (
        "🤖 AI Decision Recommendation Bot\n\n"
        "WHAT THIS BOT DOES:\n"
        "Helps you make structured, rational decisions using weighted scoring analysis.\n\n"
        "PERFECT FOR:\n"
        "✓ Choosing a course or major\n"
        "✓ Selecting a final year project topic\n"
        "✓ Deciding between internships or jobs\n"
        "✓ Choosing a university or postgraduate program\n"
        "✓ Study vs work decisions\n\n"
        "HOW IT WORKS:\n"
        "1. Describe your decision\n"
        "2. List your options (2-10)\n"
        "3. Define evaluation criteria (2-10)\n"
        "4. Weight each criterion by importance (1-10)\n"
        "5. Score each option on each criterion (1-10)\n"
        "6. Get a detailed, explainable recommendation\n\n"
        "COMMANDS:\n"
        "/start - Start a new decision analysis\n"
        "/restart - Restart the current analysis\n"
        "/cancel - Cancel and clear session\n"
        "/help - Show this help message\n\n"
        "TIPS FOR BEST RESULTS:\n"
        "• Be honest with your scoring\n"
        "• Consider both short and long-term factors\n"
        "• Weight criteria based on YOUR priorities\n"
        "• Remember: this tool helps structure your thinking\n"
        "• Final decision should include non-quantifiable factors\n\n"
        "NOTE:\n"
        "This bot provides data-driven recommendations but cannot replace your judgment.\n"
        "Use it as a decision aid, not an absolute authority."
    )
    await update.message.reply_text(help_text)


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Start the bot"""
    # Get token from environment
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable is not set")
        print("\nTo fix this:")
        print("  1. Create a .env file in the project directory:")
        print("     TELEGRAM_BOT_TOKEN=your_token_here")
        print("  2. Or set it as an environment variable:")
        print("     export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("  3. Get your token from @BotFather on Telegram")
        return

    logger.info(f"Bot token loaded successfully (length: {len(TOKEN)} chars)")

    # Create application
    application = Application.builder().token(TOKEN).build()
    logger.info("Application created successfully")

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
            WEIGHT_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_confirmation)],
            OPTION_SCORES: [MessageHandler(filters.TEXT & ~filters.COMMAND, option_scores)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("restart", restart),
            CommandHandler("help", help_command),
        ],
    )

    # Add handlers - conversation handler first (it handles /start via entry_points)
    application.add_handler(conv_handler)
    logger.info("Conversation handler added")
    # Add help handler separately so it works outside conversations
    application.add_handler(CommandHandler("help", help_command))
    logger.info("Help handler added")

    # Add error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log the error and send a message to the user"""
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
        if update and isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Sorry, an error occurred. Please try /start to begin again."
                )
            except Exception:
                pass  # Ignore errors in error handler
    
    application.add_error_handler(error_handler)
    logger.info("Error handler added")

    # Run the bot
    logger.info("Starting bot polling...")
    print("✅ Bot is starting...")
    print("📱 Press Ctrl+C to stop")
    application.run_polling(allowed_updates=[
        "message",
        "callback_query",
        "my_chat_member",
    ])


if __name__ == "__main__":
    main()
