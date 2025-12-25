# Wonderful
Home Assignment

## the aim of this project was to create a pharmacy agent that can provide information about mediations, inventory, prescriptions, and more.  

## in order to get my agent up and running, just follow the steps below:

# Clone the repo
git clone https://github.com/yonatanm-huji/Wonderful.git

# Go into the folder
cd Wonderful

# Set API key
export OPENAI_API_KEY=your-key-here

# Assuming you have docker installed and open, run Docker
docker-compose up --build

## Overview of the Project
The agent has 6 tools it can use to help customers. Each tool connects to the database to retrieve or check specific information. The agent is built using python on the backend and html on the front end. app.py is the application which incorporates the pharmacy.db, a database comprised of pharmaceutical and patient information. The database is further described below. In addition, there are six tools that the agent can call upon. Initially only three tools were built, but during testing, more limitations were unveiled that required the addition of more tools. The tooling is further detailed below.

The agent had a few requirements:
-conversational
-streaming
-english and Hebrew
-it had to be SAFE. Meaning no medical advice and it would refer to a healthcare professional when needed

## Overall results

The agent is best at providing information about the medicines themselves. When calling other tools, it is either too safe and resorts to the healthcare professional tool, or it attempts to call multiple tools and then has some hallucination. Using reAct or another multi-step framework could help with this. While some of this behavior is needed, especially for HIPAA compliance, it is likely too safe to help with important pharmacy functions.

## database

Comprised of three tables; Users Table (4 parameters), Medications Table (8 parameters), and Prescriptions Table (6 parameters). There are 10 users, 8 medications, and some sample prescriptions. 


## Tooling. 6 tools, although the agent does not use tools 4 and 5 correctly.
---

## 1. Get Medication Info

Looks up detailed information about a medication

Needs: Medication name (like "Aspirin")

Returns:
- Medication description and what it's used for
- Available forms (tablet, capsule, etc.)
- Common dosages
- Side effects
- Who shouldn't take it
- Whether it requires a prescription

If something goes wrong:Returns error message saying medication not found or database unavailable

## 2. Check Drug Interactions

What it does: Finds out what other medications could cause problems when combined

Needs: Medication name

Returns:
- Active ingredients
- List of medications that interact
- How serious the interactions are

If something goes wrong: Returns "no interactions found" if data is missing

---

## 3. Check Inventory

What it does: Checks if we have a medication in stock

Needs: Medication name

Returns:
- In stock or out of stock
- How many units available
- Status (out of stock / low stock / in stock)
- Whether it requires a prescription

If something goes wrong: Shows "out of stock" if quantity data is unavailable

---

## 4. Get User Allergies

What it does: Looks up a patient's allergies and current medications

Needs: Patient's full name (like "Jalen Brunson")

Returns:
- Patient name
- Known allergies (or "None on file")
- List of medications they're currently taking

If something goes wrong: Shows "None on file" if no allergy data exists

---

## 5. Check Prescription

What it does: Verifies if a patient has a valid prescription for a medication

Needs: Patient name AND medication name

Returns:
- Whether the medication needs a prescription
- Whether the patient has one on file
- Prescription details (doctor, date, refills left)
- Clear message about status

If something goes wrong: Defaults to requiring prescription verification (safe approach)

---

## 6. Refer to Professional

What it does: Creates referral messages when questions need a doctor or pharmacist

Needs: Type of question (diagnosis, treatment, dosage advice, etc.)

Returns:
- Appropriate referral message
- Explanation of why professional consultation is needed

If something goes wrong: This tool can't fail - always provides referral message

