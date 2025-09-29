def calculator(a, b, opn):
    """
    Perform basic arithmetic operationon two numbers.

    Args:
        a (float): First number
        b (float): Second number
        operation (str): "add", "sub", "mul", "div"

    Returns:
        float or str: Result of operation or error message
    """
    operation = operation.lower().strip()

    #operation logic
    if opn == "add":
        return a + b
    elif opn == "sub":
        return a - b
    elif opn == "mult":
        return a * b
    elif opn == "div":
        if b == 0:
            return "Error: Division by zero"
        else:
            return a / b
    else:
        return f"Error invalid operation '{operation}'. Use add, sub, mul, div"

def word_stats(text):
    """
    Analyze text and return word statistics.

    Args:
        text (str): Input text to analyze

    Returns:
        dict: Dictionary with word_count, unique words, most_common
    """

    words = text.lower().split()

    word_count = len(words)
    unique_words = len(set(words))

    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    most_common = max(word_freq, key=word_freq.get) if word_freq else None
    return {
        'word_count': word_count,
        'unique_words': unique_words, 
        'most_common': most_common
    }
