# **System Design Exercise 3 — MERIDIANO**

**Module 3 — Negative Sampling**

---

## **Context**

MERIDIANO is a news aggregator app. It indexes around 30,000 new articles per day from 400 sources, across sections like politics, sports, business and culture. 40M monthly active users.

The home feed today is the same for everyone: the biggest stories of the moment, ordered by how much traffic each one is getting.

Two things about this catalog:

* Most of an article's readership happens in its first day or two. Some stories stay relevant for a week; most do not.  
* New articles arrive continuously, all day.

**What the product team wants:** replace the current feed with a personalised one. Success is clicks per session. 

## **Data available**

**users** — `user_id`, `signup_date`, `region`, `device`

**articles** — `article_id`, `headline`, `body_text`, `source`, `section`, `author`, `region`, `tags`, `published_at`

**impressions** — `user_id`, `article_id`, `position`, `timestamp`, `clicked`, `dwell_seconds`

## **Deliverable**

1. **Describe the solution you would deliver, step by step.** What you would do first, what information you would gather, which signals you would use, which models you would choose — and why, at each step.  
2. **Describe how it runs in production.** What gets computed online, what gets computed offline, and how often each part is refreshed.  
3. **Describe how you would validate it.**

   ## **Trade-offs to defend**

1. How does your solution decide what counts as a negative example? You only ever observe clicks.  
2. How does your architecture handle a catalog where items appear, peak and fade within a day or two?  
3. How does your solution avoid converging on the same few large sources for every user?

