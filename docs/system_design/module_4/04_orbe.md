# **System Design Exercise 4 — ORBE**

**Module 4 — End to End RecSys**

---

## **Context**

ORBE is a short-video platform. 20M daily active users. The event log holds around 4 billion interactions from the last three months alone, and grows by tens of millions a day.

The home screen is an infinite feed. Latency has to be low enough that the user never perceives a wait — a feed that hesitates is a feed people stop scrolling.

A small share of creators receives the large majority of views. Everyone outside that group gets almost nothing, and they are leaving: uploads from creators outside the top tier have fallen for three straight quarters.

**What the product team wants, in order of how loudly they say it:**

1. More watch time.  
2. More engagement — likes and shares.  
3. A fix for the creator problem. Videos from outside the head of the distribution have to get real exposure, or there will be nothing left to recommend.

## **Data available**

**users** — `user_id`, `signup_date`, `age`, `region`, `language`, `device`

**videos** — `video_id`, `creator_id`, `title`, `description`, `tags`, `category`, `duration_seconds`, `language`, `published_at`, `content_embedding`

**creators** — `creator_id`, `subscriber_count`, `account_age`, `region`

**impressions** — `user_id`, `video_id`, `position`, `timestamp`, `watch_seconds`, `watch_ratio`, `liked`, `shared`

`watch_ratio` is the fraction of the video that was actually watched. `content_embedding` is a vector representation of the video itself, computed at upload time. Both are available to you and worth thinking about.

## **Deliverable**

1. **Describe the solution you would deliver, step by step.** What you would do first, what information you would gather, which signals you would use, which models you would choose — and why, at each step.  
2. **Describe the serving pipeline and its main components.** What each component does, and how the feed gets from everything available down to what the user actually sees. Include a diagram.  
3. **Describe how you would validate it.**

## **Trade-offs to defend**

1. Short videos tend to have a higher watch ratio than long ones. How does your solution avoid learning that short videos are simply better?  
2. How does your solution reconcile watch time, engagement and creator exposure when they disagree?  
3. Each load of the feed shows a handful of videos. How does your solution get from everything available down to that handful, given the latency requirement?  
4. What strategies would you use for training, given a dataset with billions of interactions?

