## Financial Tracker project

1. getLogger(name) - more like a factory that gives a specific communication channel for your program.
    -Each logger = a communication line
    -Each line has rules → where messages go, formatting, level, etc.
    -They are identified by a name eg. logger = logging.getLogger("Financial_Tracker")
2. Data persistence is storing data so it survives program restarts. In this case we will use JSON files.s
3. str(category).strip 
            -forces the category into a string
            -.strip() rermoves whitespaces
4. Learned on Variable Shadowing
    - Using the same name for a variable in "local" space (like inside a function) as I did in a "global" space (main part of my code)
    - Python will prioritize the "closest" variable, making the outer one "invisible" or "shadowed."
    - NAMING DISCIPLINE (The "PEP 8" way)
        Entity,     Convention,                    Example
        Variables   snake_case (all lowercase)     "user_balance, mpesa_api_key"
        Functions   snake_case (verbs)             "calculate_total(), save_contact()"
        Constants   UPPER_CASE                     "VAT_RATE = 0.16, MAX_RETRIE S = 3"
        Classes,    PascalCase                     "ContactBook, PaymentGateway"  
5. .keys () - only keys
   .values() - only values
   .items() - both values and keys
6. Separation of Concerns (The "Clean Engine" Principle)
        I learned that a program shouldn't be one giant "everything" file. You split your project into Storage (the muscles), Validations (the gatekeeper), and Tracker (the steering wheel).

        The Win: If I want to switch from JSON to a Database later, I only change the "Storage" file. The rest of your app doesn't even have to know.

7. Defensive Programming (The "Sanitizer")
        One of the biggest hurdles was user input crashing the app. I implemented .strip().lower() to handle "messy" humans.

        The Lesson: Never trust user input. Always "clean" it (sanitize it) before letting it the your logic or database.

8. The "NoneType" Trap & Logical Safety
    I faced the dreaded 'in <string>' requires string as left operand, not NoneType error.

    The Correction: I learned how to use str(value or "") or default dictionary values (.get(key, [])) to ensure that even if data is missing, the code doesn't explode. It’s better to check an empty string than to crash on a "Nothing" value.

9. Positional Argument Logic (The "Recipe" Order)
    I fixed a bug where validate_category was missing data because it expected two things but only got one.

    The Insight: I learned that the order in which I pass data to a function (the "signature") is a contract. If I change the contract in the validations.py file, I must update the person calling it in storage.py.

10. Case Sensitivity & Machine Logic
    I saw firsthand that Expense is not the same as expense to a computer.

    The Fix: I moved toward a "Single Source of Truth" by forcing everything to lowercase in the validators. This makes the computer more "flexible" while keeping the data consistent.

11. The Persistent State (Life after the Terminal)
    I built a system that uses JSON Persistence.

    The Concept: I learned how to turn Python dictionaries into text files and back again. This is the foundation of every app—ensuring that work isn't lost when the program closes.

12. Reading the "Crime Scene" (Error Logs)
    Toward the end, I started reading the tracebacks Myself.

    The Skill: You stopped seeing an "ERROR" as a failure and started seeing it as a set of coordinates. You learned to look at the type of error (Value, Type, Key) and the line number to find the bug.










