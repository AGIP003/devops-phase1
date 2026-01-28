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











