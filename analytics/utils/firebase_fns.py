from typing import Tuple, List, Dict, Optional
from firebase_admin import firestore
from analytics.utils.constants import FIRESTORE_COLLECTIONS, FIRESTORE_SUBCOLLECTIONS


def get_referral_data(user_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get referral data for a user.

    :param user_id: The ID of the user
    :return: Tuple (Dict containing referral data, Optional[str] error message)
    """
    try:
        from app import db
        user_ref = db.collection(FIRESTORE_COLLECTIONS['USERS']).document(user_id)
        
        # Fetch user document
        user_data = user_ref.get().to_dict()

        if not user_data:
            return None, f"User with ID {user_id} not found"
        
        referral_code = user_data['referral_details']['referral_code']
        referred_by = user_data['referral_details']['referred_by_id']
        referred_by_email = user_data['referral_details']['referred_by_email']
        
        # Fetch all referral documents
        referrals_ref = user_ref.collection(FIRESTORE_SUBCOLLECTIONS['USERS']['REFERRALS'])
        referrals_snapshot = referrals_ref.stream()

        total_referrals = 0
        tokens_earned = 0
        referral_history = []

        for referral in referrals_snapshot:
            referral_data = referral.to_dict()
            total_referrals += 1
            tokens_earned += referral_data['bonus_received']
            
            referral_history.append({
                'user_id': referral_data['referred_user_id'],
                'email': referral_data['referred_user_email'],
                'signup_date': referral_data['referred_user_signup_date'],
                'bonus_received': referral_data['bonus_received']
            })

        referral_data = {
            'total_referrals': total_referrals,
            'total_tokens_earned': tokens_earned,
            'referred_by_id': referred_by,
            'referred_by_email': referred_by_email,
            'referral_code': referral_code,
            'referral_history': referral_history
        }

        return referral_data, None
    except Exception as e:
        print(f"Error retrieving referral data: {str(e)}")
        return None, str(e)
    

def get_user_token_transactions(user_id: str, page_size: int = 10, start_after_key: Optional[str] = None) -> Tuple[List[Dict], Optional[str], Optional[str]]:
    """
    Get the token transactions for a user with pagination.

    :param user_id: The ID of the user to retrieve the token transactions
    :param page_size: Number of transactions to return per page
    :param start_after_key: Key to start after for pagination
    :return: Tuple (token transactions, next_page_key, error_message)
    """
    try:
        from app import db
        user_ref = db.collection(FIRESTORE_COLLECTIONS['USERS']).document(user_id)
        token_history_ref = user_ref.collection(FIRESTORE_SUBCOLLECTIONS['USERS']['TOKEN_HISTORY'])
        
        # Build the query
        query = token_history_ref.order_by('timestamp', direction=firestore.Query.DESCENDING)
        
        # Add pagination if we have a cursor
        if start_after_key:
            start_doc = token_history_ref.document(start_after_key).get()
            if start_doc.exists:
                query = query.start_at(start_doc)
                
        query = query.limit(page_size + 1)  # Get one extra to check if there's a next page

        # Execute query
        docs = query.stream()
        transactions = []
        next_cursor = None

        for i, doc in enumerate(docs):
            # If this is the extra document, just use it for the cursor
            if i == page_size:
                next_cursor = doc.id
                break
                
            txn_data = doc.to_dict()
            transactions.append({
                "txn_id": txn_data.get("txn_id"),
                "txn_type": txn_data.get("txn_type"),
                "amount": txn_data.get("amount"),
                "timestamp": txn_data.get("timestamp")
            })

        return transactions, next_cursor, None
    except Exception as e:
        print(f"Error fetching token transactions for user {user_id}: {str(e)}")
        return [], None, str(e)
    


    
def stream_all_user_data() -> Tuple[Optional[list], Optional[str]]:
    """
    Stream all user data from the Firestore database.

    :return: Tuple (list of user data, error_message)
    """
    try:
        from app import db
        users_ref = db.collection(FIRESTORE_COLLECTIONS['USERS'])
        users_snapshot = users_ref.stream()
        return [user.to_dict() for user in users_snapshot], None
    except Exception as e:
        print(f"Error streaming all user data: {str(e)}")
        return None, str(e)

from enum import Enum
class TokenTxnType(str, Enum):
    SIGNUP_BONUS = "signup_bonus"
    REFERRAL_BONUS = "referral_bonus"
    AFFILIATE_REFERRAL_BONUS = "affiliate_referral_bonus"
    TOKEN_USAGE = "token_usage"
    TOKEN_REFUND = "token_refund"
    TOKEN_PURCHASE = "token_purchase"
    SUBSCRIPTION_PURCHASE = "subscription_purchase"
    COMPETITION_WINNINGS = "competition_winnings"
    PAID_PARTNERSHIP_CREDITS = "paid_partnership_credits"
    VESTRA_GIVEAWAY = "vestra_giveaway"
    SECURITY_REWARD = "bug_bounty"
    AFFILIATE_GIVEAWAY = "affiliate_giveaway"
    EARLY_ACCESS_BONUS = "early_access_bonus"
    BETA_TESTER_REWARD = "beta_tester_reward"
    FEEDBACK_REWARD = "feedback_reward"
    LOYALTY_BONUS = "loyalty_bonus"
    MILESTONE_REWARD = "milestone_reward"
    PROMOTIONAL_CREDIT = "promotional_credit"
    COMMUNITY_CONTRIBUTION = "community_contribution"
    SEASONAL_BONUS = "seasonal_bonus"
    EDUCATIONAL_DISCOUNT = "educational_discount"
    ENTERPRISE_CREDIT = "enterprise_credit"

from datetime import datetime

# Convert ISO string dates to a more readable format
def format_date(iso_date: str) -> str | None:
    if iso_date:
        try:
            return datetime.fromisoformat(iso_date).strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return iso_date  # Return as-is if parsing fails
    return None
    

from typing import Tuple, Dict, Optional


def get_user_referral_data(user_id: str) -> Tuple[Dict, Optional[str]]:
    """
    Get referral data for a user.

    :param user_id: The ID of the user
    :return: Tuple (Dict containing referral data, Optional[str] error message)
    """
    try:
        # Fetch referral data from Firestore
        referral_data, _ = get_referral_data(user_id)
        
        if not referral_data:
            return {
                "referrer_id": None,
                "referrer_email": None,
                "no_of_referrals": 0,
                "latest_referral_date": None,
                "last_referred_user_id": None,
                "last_referred_user_email": None
            }, None

        no_of_referrals = referral_data.get('total_referrals', 0)
        referrer_id = referral_data.get('referred_by_id')
        referrer_email = referral_data.get('referred_by_email')
        
        referral_history = referral_data.get('referral_history', [])
        latest_referral_date = None
        last_referred_user_id = None 
        last_referred_user_email = None

        if referral_history:
            latest_referral = max(referral_history, key=lambda ref: ref.get('signup_date', ''))
            latest_referral_date = latest_referral.get('signup_date')
            last_referred_user_id = latest_referral.get('user_id')
            last_referred_user_email = latest_referral.get('email')

        return {
            "referrer_id": referrer_id,
            "referrer_email": referrer_email,
            "no_of_referrals": no_of_referrals,
            "latest_referral_date": format_date(latest_referral_date),
            "last_referred_user_id": last_referred_user_id,
            "last_referred_user_email": last_referred_user_email,
        }, None

    except Exception as e:
        return None, f"Error retrieving referral data: {str(e)}"

from typing import Tuple, Dict, Optional


def get_token_transactions(user_id: str) -> Tuple[Dict, Optional[str]]:
    """
    Get token transactions for a user.

    :param user_id: The ID of the user
    :return: Tuple (List of token transactions, Optional[str] error message)
    """
    try:
        token_transactions = []
        page_token = None

        # Fetch all token transactions for the user
        while True:
            transactions, next_page_token, _ = get_user_token_transactions(user_id, page_size=100, start_after_key=page_token)
            token_transactions.extend(transactions)
            if not next_page_token or next_page_token == page_token:
                break
            page_token = next_page_token

        # Split transactions by type for more efficient processing
        usage_txns = []
        purchase_txns = []
        for txn in token_transactions:
            if txn['txn_type'] == TokenTxnType.TOKEN_USAGE.value:
                usage_txns.append(txn)
            elif txn['txn_type'] == TokenTxnType.TOKEN_PURCHASE.value:
                purchase_txns.append(txn)

        # Calculate metrics in single pass through filtered lists
        token_usage_count = abs(sum(txn['amount'] for txn in usage_txns))
        token_purchase_count = sum(txn['amount'] for txn in purchase_txns)
        last_token_usage = max((txn['timestamp'] for txn in usage_txns), default=None)
        last_token_purchase = max((txn['timestamp'] for txn in purchase_txns), default=None)

        return {
            "token_usage_count": token_usage_count,
            "token_purchase_count": token_purchase_count,
            "token_purchase_history": purchase_txns,
            "last_token_usage": format_date(last_token_usage), 
            "last_token_purchase": format_date(last_token_purchase),
        }, None

    except Exception as e:
        return None, f"Error retrieving token transactions: {str(e)}"


from typing import Tuple, Dict, Optional

def get_user_details(user_data: Dict) -> Tuple[Dict, Optional[str]]:
    """
    Extracts user details from the provided user data dictionary.
    
    Args:
        user_data (dict): A dictionary containing user data.
        
    Returns:
        tuple: A tuple containing username, email, signup date, and token balance.
    """
    try:
        # Check if required keys are present in the dictionary
        required_keys = ['user_details', 'created_at', 'token_details']
        for key in required_keys:
            if key not in user_data:
                raise KeyError(f"Missing required key: {key}")
            
        username = user_data.get('user_details', {}).get('username')
        email = user_data.get('user_details', {}).get('email')
        signup_date = user_data.get('created_at')
        token_balance = user_data.get('token_details', {}).get('token_balance', 0)
        
        return {
            "username": username,
            "email": email,
            "signup_date": signup_date,
            "token_balance": token_balance,
        }, None

    except (ValueError, KeyError) as e:
        return None, f"Error extracting user details: {str(e)}"

