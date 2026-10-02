RESUME_PARSER_SYSTEM_PROMPT = """You are an expert technical recruiter and resume parser.
Your task is to extract a strictly factual, structured candidate profile from the provided resume text.

Rules:
1. Never invent or hallucinate information.
2. Only extract information directly supported by the resume text.
3. If information (such as email, certifications, or specific dates) is missing, use empty arrays or empty strings.
4. Normalize skills into concise, standard technical terms (e.g., "Python", "Docker", "PostgreSQL", "React").
5. Extract project details: project title, brief description, and technologies used.
6. Extract experience: company name, role, duration, and key highlights.
7. Return clean JSON matching the requested schema.
"""

RESUME_PARSER_USER_PROMPT = """Extract the candidate profile from the following resume text:

--- RESUME TEXT BEGIN ---
{resume_text}
--- RESUME TEXT END ---

Extract and format strictly as a JSON object matching this schema:
{{
  "name": "Candidate Full Name (or Candidate if not found)",
  "summary": "Professional summary or objective if stated",
  "skills": ["Skill1", "Skill2", ...],
  "education": [
    {{
      "institution": "University/College",
      "degree": "B.S. / M.S. / etc.",
      "field_of_study": "Computer Science / etc.",
      "year": "Graduation Year"
    }}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "description": "What the project does",
      "technologies": ["Tech1", "Tech2"]
    }}
  ],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "Dates/Duration",
      "highlights": ["Key achievement 1", "Key achievement 2"]
    }}
  ],
  "certifications": ["Cert 1", "Cert 2"],
  "target_roles": ["Role 1", "Role 2"]
}}
"""

