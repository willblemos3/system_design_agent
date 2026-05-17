# =========================
# schemas.py
# =========================

CANDIDATE_SCHEMA = {
    "description": "Candidate index",

    "fields": [
        {
            "name": "candidate_id",
            "type": "string",
            "primary": True,
            "max_length": 100,
        },
        {
            "name": "external_id",
            "type": "int64",
        },
        {
            "name": "first_name",
            "type": "string",
            "max_length": 100,
        },
        {
            "name": "last_name",
            "type": "string",
            "max_length": 100,
        },
        {
            "name": "content",
            "type": "string",
            "max_length": 8000,
        },
        {
            "name": "embedding",
            "type": "vector",
            "dim": 3072,
        },
        {
            "name": "full_experience",
            "type": "json",
        },
    ],

    "vector_field": "embedding",

    "metric_type": "COSINE",
}


MEMORY_SCHEMA = {
    "description": "User conversation memory",

    "fields": [
        {
            "name": "id",
            "type": "string",
            "primary": True,
            "max_length": 100,
        },
        {
            "name": "user_id",
            "type": "string",
            "max_length": 200,
        },
        {
            "name": "session_id",
            "type": "string",
            "max_length": 200,
        },
        {
            "name": "role",
            "type": "string",
            "max_length": 20,
        },
        {
            "name": "text",
            "type": "string",
            "max_length": 8000,
        },
        {
            "name": "timestamp",
            "type": "string",
            "max_length": 50,
        },
        {
            "name": "embedding",
            "type": "vector",
            "dim": 3072,
        },
    ],

    "vector_field": "embedding",

    "metric_type": "COSINE",
}



EXPERIENCE_SCHEMA = {
    "description": "Individual work experience index",

    "fields": [
        {
            "name": "experience_id",
            "type": "string",
            "primary": True,
            "max_length": 100,
        },
        {
            "name": "candidate_id",
            "type": "string",
            "max_length": 100,
        },
        {
            "name": "experience",
            "type": "json",
        },
        {
            "name": "embedded_content",
            "type": "vector",
            "dim": 3072,
        },
    ],

    "vector_field": "embedded_content",

    "metric_type": "COSINE",
}


# =========================
# JOB_SCHEMA
# =========================

JOB_SCHEMA = {
    "description": "Job index",

    "fields": [
        {
            "name": "id",
            "type": "int64",
            "primary": True,
            "auto_id": True,
        },
        {
            "name": "job_title",
            "type": "string",
            "max_length": 200,
        },
        {
            "name": "job_content",
            "type": "string",
            "max_length": 5000,
        },
        {
            "name": "embedding",
            "type": "vector",
            "dim": 3072,
        },
    ],

    "vector_field": "embedding",

    "metric_type": "COSINE",
}