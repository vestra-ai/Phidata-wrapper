from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, jsonify
from datetime import datetime
from firebase_admin import firestore
from analytics.utils.constants import FIRESTORE_COLLECTIONS
from analytics.utils.firebase_fns import get_user_details, get_token_transactions,stream_all_user_data, get_user_referral_data
from utils.save_to_storage import upload_csv_to_bucket
from ratelimit import limits
from ratelimit.exception import RateLimitException
from analytics.utils.filehand import convert_to_csv

TEN_MINUTES = 600

analytics_user_bp = Blueprint('analytics_user', __name__, url_prefix='/analytics/users')

@analytics_user_bp.route('/all-users-details', methods=['GET'])
@limits(calls=30, period=900)
def get_all_user_details():
    """
    Get details for all users and save as CSV in storage.
    """
    try:
        # Get all user data
        all_user_data, error = stream_all_user_data()

        if error:
            print(f"Error streaming all user data: {error}")
            return jsonify({"success": False, "error": "Error retrieving user data"}), 500

        all_user_details = []

        for user_data in all_user_data:
            user_id = user_data.get('user_id')

            # Fetch user details, token details, and referral data in parallel
            with ThreadPoolExecutor() as executor:
                user_details_future = executor.submit(get_user_details, user_data)
                token_details_future = executor.submit(get_token_transactions, user_id)
                referral_data_future = executor.submit(get_user_referral_data, user_id)

                user_details, user_details_err = user_details_future.result()
                token_details, token_details_err = token_details_future.result()
                referral_data, referral_data_err = referral_data_future.result()

                if user_details_err:
                    print(f"Error fetching user details for user_id {user_id}: {user_details_err}")
                    raise Exception(f"Error fetching user details for user_id {user_id}: {user_details_err}")
                
                if token_details_err:
                    print(f"Error fetching token details for user_id {user_id}: {token_details_err}")
                    raise Exception(f"Error fetching token details for user_id {user_id}: {token_details_err}")
                
                if referral_data_err:
                    print(f"Error fetching referral data for user_id {user_id}: {referral_data_err}")
                    raise Exception(f"Error fetching referral data for user_id {user_id}: {referral_data_err}")

            # Combine all responses into a single dictionary and append to the list
            combined_user_details = {
                **user_details,
                **token_details,
                **referral_data,
                "user_id": user_id
            }
            all_user_details.append(combined_user_details)

        # Upload CSV to storage
        csv_filename = "admin/files/all_staging_user_details_3.csv"
        csv_string = convert_to_csv(all_user_details)
        bucket_path = upload_csv_to_bucket(csv_string, csv_filename)

        return jsonify({"success": True, "data": {"csv_url": bucket_path}, "message": "User details retrieved and saved as CSV successfully"}), 200
    except Exception as e:
        print(f"Error retrieving all user details: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
