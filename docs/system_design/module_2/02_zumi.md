# **System Design Exercise 2 — ZUMI**

**Module 2 — Basic Models**

---

## **Context**

ZUMI is a food delivery app. Around 15,000 restaurants, 800,000 monthly active users, 2.5M orders per month.

The home feed today is a single list sorted by distance and rating. It is the same logic for everyone.

Two facts the data team keeps repeating:

* A typical user's top 3 restaurants account for about 60% of their orders.  
* Order volume and what people order swing hard by hour of day and day of week.

The growth lead's request: **more orders per user per month.** He has not been more specific than that, and when pushed he says that is your job to figure out.

## **Data available**

**users** — `user_id`, `signup_date`, `delivery_address`, `region`

**restaurants** — `restaurant_id`, `cuisine_type`, `price_range`, `avg_rating`, `delivery_radius_km`, `opening_hours`

**orders** — `order_id`, `user_id`, `restaurant_id`, `order_value`, `timestamp`

**order\_items** — `order_id`, `dish_id`, `dish_name`, `dish_category`, `price`

**events** — `user_id`, `restaurant_id`, `event_type` ∈ {view, add\_to\_cart, order}, `timestamp`

## **Deliverable**

1. **What questions would you raise before starting?** The request as stated is not enough to build from. List what you would need to pin down, and with whom.  
2. **Describe the solution you would deliver, step by step.** What you would do first, what information you would gather, which signals you would use, which models you would choose — and why, at each step.  
3. **Describe how you would validate it.**

Not asked for: code, model equations, accuracy numbers.

## **Trade-offs to defend**

1. Your top recommendation for most users turns out to be the restaurant they already order from every week. Is that a good recommendation? What is that slot worth?  
2. At any given moment, a large share of the catalog cannot serve a given user — wrong address, closed right now. How does your system handle that?  
3. Same user, 8am on a Tuesday and 11pm on a Saturday. Does your solution return something different? What does it need in order to?

---

## **Instructor notes — not for students**

The step up from Exercise 1 is not the modelling — it is that **the brief is underspecified on purpose**, and deliverable 1 is where that gets graded.

* *Restaurants or dishes?* The data supports both. Recommending restaurants and recommending dishes are different problems with different catalog sizes, different sparsity, and different repeat behavior. Nothing in the brief chooses.  
* *Which lever?* "More orders per user per month" can mean more users ordering at all, existing users ordering more often, or reactivating users who stopped. These point at different systems.  
* *Where does it go?* The home feed is the obvious surface, but nobody said so.  
* *What is the unit of success?* Orders is what was asked for. Whether revenue, retention or margin is what is actually wanted is not stated.