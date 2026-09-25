# **System Design Exercise 1 — NORVA**

**Module 1 — Recommender System Introduction and Evaluation Metrics**

---

## **Context**

NORVA is an online clothing retailer. Around 40,000 items, 180,000 orders per month.

The homepage carousel is picked by hand every Monday by two merchandisers — the same 30 items for every user. The cart page has nothing.

You are the first ML engineer. Two requests arrive in the same week:

* **Homepage.** The merchandising director wants it to stop being hand-picked, and she doubts an algorithm will beat her team.  
* **Cart page.** The head of e-commerce wants a module that gets people to add one more item before checkout.

## **Data available**

**users** — `user_id`, `signup_date`, `country`, `gender` (self-declared, often missing)

**items** — `item_id`, `brand`, `price`, `category_path`, `color`

**transactions** — `order_id`, `user_id`, `item_id`, `timestamp`

**events** — `user_id`, `item_id`, `event_type` ∈ {view, add\_to\_cart, purchase}, `timestamp`

No ratings, no reviews.

## **Deliverable**

1. **Describe the solution you would deliver, step by step.** What you would do first, what information you would gather, which signals you would use, which models you would choose — and why, at each step.  
2. **Describe how you would validate it.**

## **Trade-offs to defend**

1. Why is your solution better than just showing the best sellers?  
2. Suppose the cart module recommends items the user was already going to buy. Your offline metric looks excellent. Did the business gain anything? How would you find out?  
3. A user is looking at a t-shirt. What belongs next to it on the homepage, and what belongs next to it in the cart? Same answer or different?

