# src/main.py
from recommender import Recommender
from data_loader import load_data


def main():
    article_metadata, clicks_data = load_data()
    recommender = Recommender(article_metadata, clicks_data)

    while True:
        user_id = input("Enter a user ID (or 'q' to quit): ")
        if user_id.lower() == "q":
            break

        try:
            user_id = int(user_id)
            recommendations = recommender.recommend(user_id)
            print(f"Recommendations for user {user_id}:")
            print(recommendations)
            # print(recommendations[["article_id", "category_id", "publisher_id", "words_count", "score"]])
            print()
        except ValueError:
            print("Invalid user ID. Please enter a valid integer.")
        except IndexError:
            print(f"No recommendations found for user {user_id}.")


if __name__ == "__main__":
    main()
