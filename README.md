# Stress Management & Personalized Wellness Platform

## Overview

This project is a personalized stress-management platform designed to
help users understand their stress levels and follow personalized
interventions to improve their well-being.

The system combines:

-   **MongoDB** for data persistence
-   **Machine Learning** for stress-level prediction
-   **LLM integration** for personalized intervention generation
-   **Backend APIs** for application logic
-   **Frontend application** for user interaction

The primary goal is not to make AI the product.

> **AI is used as a personalization engine. The product is the system
> that helps the user manage and reduce stress.**

------------------------------------------------------------------------

## Product Philosophy

The system should not require an AI call for every user interaction.

Instead, the system follows this approach:

``` text
User Assessment
      ↓
Machine Learning Prediction
      ↓
Personalized Intervention Generation
      ↓
15 Personalized Interventions
      ↓
7-Day Weekly Plan
      ↓
Repeated Practice and Progress Tracking
      ↓
Periodic Reassessment
      ↓
New Personalized Intervention Pool
```

AI is used when personalization needs to be generated or updated, not
for every simple operation.

This reduces:

-   AI API costs
-   Token usage
-   System complexity
-   Unnecessary latency

It also allows users to build habits through repeated activities instead
of receiving completely new activities every week.

------------------------------------------------------------------------

# Core System Architecture

The system uses separate MongoDB collections based on domain and
purpose.

``` text
Database
│
├── users
├── profiles
├── stress_assessments
├── journeys
├── intervention_pools
├── weekly_plans
├── achievements
└── user_statistics
```

All user-related objects are connected using a common `user_id`.

The system does **not** use:

``` text
❌ One collection per user
❌ One giant user document containing all application data
❌ Mobile number as the relationship key across every collection
```

The canonical relationship identifier is:

``` text
user_id
```

------------------------------------------------------------------------

# Database Collections

## 1. `users`

Responsible for authentication and identity.

### Responsibilities

-   User registration
-   Login
-   Authentication
-   Account status

### Example

``` json
{
  "_id": "ObjectId(...)",
  "mobile_no": "7498253835",
  "email": "user@example.com",
  "password_hash": "...",
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

### Does not contain

``` text
❌ Age
❌ Stress level
❌ Assessment features
❌ Tasks
❌ Streak
```

### Important indexes

``` text
mobile_no → unique
email → unique where applicable
```

------------------------------------------------------------------------

## 2. `profiles`

Contains relatively stable personal information.

### Example

``` json
{
  "_id": "ObjectId(...)",
  "user_id": "ObjectId(...)",
  "name": "User Name",
  "dob": "2004-08-05",
  "gender": "male",
  "created_at": "...",
  "updated_at": "..."
}
```

### Design decisions

Age is not stored because it can be calculated from the date of birth.

``` text
dob → calculate age when required
```

A user should have one profile.

``` text
user_id → unique
```

------------------------------------------------------------------------

## 3. `stress_assessments`

Stores historical stress assessments.

The assessment contains the features used by the Machine Learning model
and the resulting prediction.

### Example

``` json
{
  "_id": "ObjectId(...)",
  "user_id": "ObjectId(...)",

  "features": {
    "anxiety": 10,
    "self_esteem": 9,
    "mental_health_history": 1,
    "depression": 10,
    "sleep_quality": 3
  },

  "stress_score": 72,
  "stress_level": 2,

  "model_version": "v1.0",

  "created_at": "..."
}
```

### Important principle

Assessment data should not overwrite previous assessments.

Example:

``` text
Assessment 1 → Stress Level 3
Assessment 2 → Stress Level 2
Assessment 3 → Stress Level 1
```

This allows the system to track the user's stress progression over time.

------------------------------------------------------------------------

# 4. `journeys`

A journey represents a larger phase of the user's stress-management
process.

A journey is created based on an assessment and its resulting
personalization.

``` text
Assessment
    ↓
Journey
    ↓
Intervention Pool
    ↓
Weekly Plans
```

### Example lifecycle

``` text
Journey 1
│
├── Assessment A
│
├── Intervention Pool
│
├── Week 1
├── Week 2
├── Week 3
└── Week 4
        ↓
   Reassessment
        ↓
New Journey / New Intervention Pool
```

A journey may remain active until the user is reassessed or the system
determines that a new personalization cycle is required.

------------------------------------------------------------------------

# 5. `intervention_pools`

This is one of the most important concepts in the system.

The Machine Learning model predicts the user's stress level.

The LLM then generates approximately **15 personalized interventions**
based on:

-   User assessment features
-   Predicted stress level
-   User context
-   Potentially previous user feedback and preferences

These 15 interventions are not necessarily 15 activities the user must
complete.

They are a personalized pool of options.

``` text
Personalized Intervention Pool
│
├── Intervention 1
├── Intervention 2
├── Intervention 3
├── ...
└── Intervention 15
```

### Example

``` text
Intervention Pool
│
├── Walking
├── Breathing Exercise
├── Journaling
├── Meditation
├── Social Connection
├── Creative Expression
├── Sleep Hygiene
├── Progressive Muscle Relaxation
├── Mindful Observation
├── Career Planning
├── Yoga
├── Music
├── Nature Walk
├── Self-Compassion
└── Digital Detox
```

The interventions are personalized for the specific user and assessment.

------------------------------------------------------------------------

# 6. `weekly_plans`

A weekly plan selects 7 interventions from the personalized intervention
pool.

``` text
15 Personalized Interventions
          ↓
7 Active Interventions
          ↓
Weekly Plan
```

### Example

``` text
Monday    → Breathing Exercise
Tuesday   → Walking
Wednesday → Journaling
Thursday  → Meditation
Friday    → Social Connection
Saturday  → Creative Expression
Sunday    → Sleep Hygiene
```

The remaining interventions are available as alternatives.

``` text
7 active interventions
8 alternative interventions
```

------------------------------------------------------------------------

## Reusing Weekly Interventions

The same interventions can be reused in subsequent weeks.

Example:

``` text
Week 1:
Monday    → Walking
Tuesday   → Breathing
Wednesday → Journaling

Week 2:
Monday    → Walking
Tuesday   → Breathing
Wednesday → Journaling
```

This is intentional.

The goal is to help users:

-   Repeat useful activities
-   Build habits
-   Track consistency
-   Determine which interventions work for them

The system should not generate completely new interventions every week
unless there is a reason to update personalization.

------------------------------------------------------------------------

# Intervention Replacement

Users should be able to replace an intervention they dislike or cannot
perform.

Example:

``` text
Meditation
    ↓
User selects "Replace"
    ↓
System shows available alternatives
    ↓
User selects Breathing Exercise
```

This should not require another LLM call.

The system can simply use one of the remaining personalized
alternatives.

### Important

The original assignment should not be permanently erased.

The system should preserve the replacement history.

Example:

``` json
{
  "original_intervention_id": "MEDITATION",
  "current_intervention_id": "BREATHING",
  "replacement_reason": "USER_DISLIKE"
}
```

This allows the system to learn user preferences.

For example:

``` text
User repeatedly rejects meditation.
User consistently chooses walking.
```

This information can be used during future personalization.

------------------------------------------------------------------------

# Task Execution History

The intervention may be reused, but the execution history must be
preserved.

Example:

``` text
Walking Intervention
│
├── Week 1 → Completed
├── Week 2 → Completed
├── Week 3 → Skipped
└── Week 4 → Completed
```

The system should not overwrite the same task record repeatedly.

Historical execution data can be used for:

-   Current streak
-   Longest streak
-   Completion rate
-   Preferred activities
-   Skipped activities
-   Future personalization

------------------------------------------------------------------------

# 7. `achievements`

Stores unlocked achievements.

### Example

``` json
{
  "_id": "ObjectId(...)",
  "user_id": "ObjectId(...)",
  "achievement_code": "STREAK_7",
  "unlocked_at": "..."
}
```

Possible achievements:

``` text
7-day streak
30 tasks completed
First assessment
Completed first journey
```

------------------------------------------------------------------------

# 8. `user_statistics`

Stores fast-access derived metrics used by the dashboard.

### Example

``` json
{
  "user_id": "ObjectId(...)",
  "current_streak": 7,
  "longest_streak": 21,
  "total_tasks_completed": 53,
  "updated_at": "..."
}
```

The underlying task execution history remains the source of truth.

Statistics are maintained to make dashboard queries faster.

------------------------------------------------------------------------

# Complete Product Flow

``` text
User
  ↓
Register / Login
  ↓
Profile
  ↓
Stress Assessment
  ↓
Machine Learning Prediction
  ↓
Create Journey
  ↓
LLM Generates 15 Personalized Interventions
  ↓
Store Intervention Pool
  ↓
Select 7 Interventions for Weekly Plan
  ↓
User Performs Daily Activities
  ↓
User Can:
    ├── Complete
    ├── Skip
    ├── Replace
    └── Provide Feedback
  ↓
Track Progress
  ↓
Periodic Reassessment
  ↓
Generate New Personalized Intervention Pool
```

------------------------------------------------------------------------

# Machine Learning Integration

The ML model is responsible for predicting stress.

``` text
Assessment Features
        ↓
ML Model
        ↓
Stress Score
        ↓
Stress Level
```

Example:

``` text
Input:
    anxiety
    depression
    sleep quality
    social support
    etc.

Output:
    stress_score
    stress_level
```

The ML model should be implemented as a separate service or module.

The ML logic should not be scattered randomly throughout API routes.

------------------------------------------------------------------------

# LLM Integration

The LLM is responsible for generating personalized interventions.

``` text
Assessment Features
        ↓
ML Prediction
        ↓
User Context
        ↓
Prompt Builder
        ↓
LLM
        ↓
Structured Output
        ↓
Validation
        ↓
Intervention Pool
```

The system should never blindly store raw LLM output.

The output must be validated.

Example validation rules:

``` text
Exactly 15 interventions
Every intervention has a title
Every intervention has a description
Subtasks are valid
No malformed output
```

The LLM should return structured data rather than free-form text.

------------------------------------------------------------------------

# Recommended Development Roadmap

## Phase 1 --- Database

Implement:

``` text
users
profiles
stress_assessments
```

Required operations:

``` text
Create user
Get user
Update profile
Create assessment
Get assessment history
```

------------------------------------------------------------------------

## Phase 2 --- Machine Learning Integration

Example flow:

``` text
POST /assessments
        ↓
Validate input
        ↓
Save assessment
        ↓
Send features to ML model
        ↓
Receive prediction
        ↓
Save stress result
```

------------------------------------------------------------------------

## Phase 3 --- LLM Integration

Example flow:

``` text
Assessment
    ↓
ML Result
    ↓
User Context
    ↓
Prompt Builder
    ↓
LLM
    ↓
Structured Output
    ↓
Validation
    ↓
intervention_pools
```

------------------------------------------------------------------------

## Phase 4 --- Journey and Intervention Pool

Implement:

``` text
Create Journey
Generate 15 Interventions
Validate LLM Output
Store Intervention Pool
Retrieve Active Intervention Pool
```

------------------------------------------------------------------------

## Phase 5 --- Weekly Plans

Implement:

``` text
Select 7 interventions
Assign dates
Create weekly plan
Retrieve today's intervention
```

Example endpoint:

``` text
GET /weekly-plan?date=2026-07-20
```

------------------------------------------------------------------------

## Phase 6 --- User Interaction

Implement:

``` text
Complete intervention
Skip intervention
Replace intervention
Provide feedback
```

This is where the system becomes a real application rather than simply:

``` text
Input → ML → LLM → Output
```

------------------------------------------------------------------------

# MVP Scope

The first working version should contain:

``` text
Register / Login
        ↓
Profile
        ↓
Stress Assessment
        ↓
ML Prediction
        ↓
LLM Generates 15 Interventions
        ↓
Create 7-Day Plan
        ↓
View Today's Intervention
        ↓
Complete / Skip / Replace
        ↓
Progress Dashboard
```

Do not initially overbuild:

``` text
❌ Complex achievement systems
❌ Advanced recommendation learning
❌ Multiple dashboards
❌ Notifications
❌ Unnecessary AI calls
❌ Excessive microservices
```

First make the core loop work end-to-end.

------------------------------------------------------------------------

# Development Philosophy

This project is not simply an ML project.

It is a software system containing:

-   A backend
-   A database
-   Authentication
-   An ML component
-   An LLM component
-   Business logic
-   A frontend
-   Testing
-   Deployment

The ML model and LLM are only components of the complete application.

A good model inside a badly designed application still results in a bad
product.

The recommended development approach is:

``` text
Database Schema
      ↓
CRUD Operations
      ↓
API Layer
      ↓
ML Service
      ↓
LLM Service
      ↓
Business Logic
      ↓
Frontend
      ↓
Testing
      ↓
Deployment
```

Build one complete vertical slice at a time.

Example:

``` text
Register
   ↓
Login
   ↓
Get Profile
   ↓
Submit Assessment
   ↓
Get ML Result
```

Once this works correctly, move to the next slice.

------------------------------------------------------------------------

# Final System Architecture

``` text
                         ┌─────────────────────┐
                         │        users        │
                         │ Authentication      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      profiles       │
                         │ Personal Information│
                         └─────────────────────┘

                                    │
                                    ▼

                         ┌─────────────────────┐
                         │ stress_assessments  │
                         │ Features + ML Result│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      journeys       │
                         │ Stress Management   │
                         │ Lifecycle           │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ intervention_pools  │
                         │ 15 Personalized     │
                         │ Interventions       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    weekly_plans     │
                         │ 7 Active Activities │
                         │ + Alternatives      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ User Execution      │
                         │ Complete / Skip /   │
                         │ Replace / Feedback  │
                         └──────────┬──────────┘
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                ┌─────────────────┐   ┌─────────────────┐
                │ user_statistics │   │  achievements   │
                │ Streaks/Metrics │   │ Unlocked Goals │
                └─────────────────┘   └─────────────────┘
```

------------------------------------------------------------------------

## Core Principle

> **Use Machine Learning to understand the user's stress. Use the LLM to
> personalize interventions. Use the application to help the user build
> habits and improve over time.**

The system should optimize for user improvement, not AI usage.
