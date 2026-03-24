# Recommendations Architecture

## 1. Identity

- **What it is:** Five rule-based recommendation endpoints for authenticated users.
- **Purpose:** Surface books through rating-based, category-based, history-based, and similarity-based heuristics.

## 2. Core Components

- `backend/app/api/recommendations.py:13-127` -- All five recommendation handlers.
- `backend/app/models/book.py:25-66` -- `Book`, `Category`, and `book_category`.
- `backend/app/models/reading.py:17-37` -- `ReadingProgress` and `ReadingStatus` used for personalization.
- `backend/app/schemas/book.py:27-46` -- Shared response models.

## 3. Algorithms

All endpoints require authentication and accept `count` in the range `1..50`.

### 3.1 Random

- Query top-rated books at `backend/app/api/recommendations.py:22-26`.
- Randomly sample that pool in Python at `backend/app/api/recommendations.py:31-32`.
- Fall back to `ORDER BY func.random()` when no rated books exist at `backend/app/api/recommendations.py:28-29`.

### 3.2 Category-Based

- Uses a direct join on `book_category` at `backend/app/api/recommendations.py:44-47`.
- Filters to books in the category with non-null ratings.
- Orders by `Book.rating.desc()` and limits in SQL.

### 3.3 Trending

- Single SQL query at `backend/app/api/recommendations.py:57-62`.
- Requires both `rating` and `rating_count`.
- Orders by `rating DESC, rating_count DESC`.

### 3.4 Personalized

- Loads completed books for the current user through a join with `ReadingProgress` at `backend/app/api/recommendations.py:75-78`.
- Falls back to trending when the user has no completed books at `backend/app/api/recommendations.py:80-81`.
- Builds a category subquery from read books at `backend/app/api/recommendations.py:83-86`.
- Retrieves unread books from those categories with a distinct SQL query at `backend/app/api/recommendations.py:88-93`.

### 3.5 Similar

- Loads the target book at `backend/app/api/recommendations.py:105-107`.
- Collects category ids through the join table at `backend/app/api/recommendations.py:109-112`.
- Builds a single query with `OR` conditions for same-author and same-category matches at `backend/app/api/recommendations.py:114-126`.

## 4. Design Notes and Limits

- The implementation is still rule-based; there is no ML ranking model.
- Category-based, personalized, and similar endpoints now push most filtering and ordering into SQL instead of walking ORM relationship collections in memory.
- Random recommendations still rely partly on Python sampling after fetching a candidate pool.
- Personalized recommendations only consider books marked `ReadingStatus.COMPLETED`.
- No recommendation endpoint writes user feedback or interaction signals back into the database.
