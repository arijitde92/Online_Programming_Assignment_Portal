from langchain_anthropic import ChatAnthropic
import textwrap
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def format_response(text):
    """
    Format the response text with proper newlines and indentation, wrapped in HTML pre tag.

    Args:
        text (str): The response text to format

    Returns:
        str: Formatted text wrapped in HTML pre tag
    """

    # Split into lines and remove empty lines at start/end
    lines = text.strip().split("\n")

    # Remove common leading whitespace
    min_indent = float("inf")
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)

    # Apply consistent indentation and wrap text
    formatted_lines = []
    for line in lines:
        if line.strip():
            # Remove common leading whitespace and add 2 spaces indentation
            base_line = "  " + line[min_indent:].rstrip()
            # Wrap text at 120 characters
            wrapped_lines = textwrap.wrap(base_line, width=120)
            formatted_lines.extend(wrapped_lines)
        else:
            formatted_lines.append("")

    # Join lines
    formatted_text = "\n".join(formatted_lines)
    return f"{formatted_text}"


class CodeAnalyzer:
    def __init__(self):
        """Initialize the code analyzer with a single model instance."""
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",  # type: ignore
            temperature=0.5,
            max_tokens=2048,  # type: ignore
            timeout=None,
            max_retries=2,
        )
        self.code_content = None
        self.code_analysis = None

    def load_code(self, filepath, debug=False):
        """
        Load and analyze the code file.

        Args:
            filepath (str): Path to the C file to analyze
            debug (bool): Whether to print debug information

        Returns:
            bool: True if code was loaded and analyzed successfully
        """
        try:
            with open(filepath, "r") as file:
                self.code_content = file.read()
            if debug:
                print("Loaded file:", filepath)
                print("Code content length:", len(self.code_content))

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """Please analyze the following C code and provide feedback within 200 words overall on the following points:
                1. Code structure and organization
                2. Naming conventions
                3. Error handling
                4. Memory management
                5. Best practices         
                Please provide a comprehensive analysis focusing on these aspects.
                Provide only the feedback and nothing else.""",
                    ),
                    ("human", "Code to analyze:\n{code}"),
                ]
            )

            if debug:
                print(prompt.invoke({"code": self.code_content}))

            chain = prompt | self.llm
            response = chain.invoke({"code": self.code_content})
            self.code_analysis = format_response(response.content)
            if debug:
                print("Code analysis completed")
            return True

        except Exception as e:
            self.code_analysis = f"Error analyzing code: {str(e)}"
            if debug:
                print("Error in load_code:", str(e))
            return False

    def analyze_compilation_error(self, compile_errors, debug=False):
        """
        Analyze compilation errors with context from the code analysis.

        Args:
            compile_errors (str): Compilation error output from gcc
            debug (bool): Whether to print debug information

        Returns:
            str: Hints for fixing the compilation errors
        """
        try:
            if debug:
                print("Analyzing compilation errors")
                print("Error length:", len(compile_errors))

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """As a programming mentor, analyze the following C compilation errors in the context of the code 
                and its previous analysis. Provide helpful hints for fixing them. DO NOT provide the complete solution, 
                only give hints that will help the student learn and understand how to fix the errors themselves.

                Focus on:
                1. Explaining the type of error in simple terms
                2. Providing hints about where to look for the issue
                3. Suggesting general approaches to fix similar errors
                4. Mentioning relevant C programming concepts to review
                5. Relating the error to the code structure and patterns identified in the analysis
                Provide the feedback within 100 words.
                Remember: Provide only hints and guidance, not complete solutions.
                Provide only the feedback and nothing else.""",
                    ),
                    (
                        "human",
                        """Previous code analysis:
                {code_analysis}

                Code:
                {code}

                Compilation errors:
                {errors}""",
                    ),
                ]
            )

            if debug:
                print(
                    prompt.invoke(
                        {
                            "code": self.code_content,
                            "code_analysis": self.code_analysis,
                            "errors": compile_errors,
                        }
                    )
                )

            chain = prompt | self.llm
            response = chain.invoke(
                {
                    "code": self.code_content,
                    "code_analysis": self.code_analysis,
                    "errors": compile_errors,
                }
            )

            if debug:
                print("Compilation error analysis completed")
            return format_response(response.content)

        except Exception as e:
            if debug:
                print("Error in analyze_compilation_error:", str(e))
            return f"Error analyzing compilation errors: {str(e)}"

    def analyze_runtime_error(self, runtime_errors, test_input=None, debug=False):
        """
        Analyze runtime errors with context from the code analysis.

        Args:
            runtime_errors (str): Runtime error output from the program
            test_input (str, optional): Input that caused the runtime error
            debug (bool): Whether to print debug information

        Returns:
            str: Hints for fixing the runtime errors
        """
        try:
            if debug:
                print("Analyzing runtime errors")
                print("Error length:", len(runtime_errors))
                print("Test input:", test_input if test_input else "No input provided")

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """As a programming mentor, analyze the following C runtime errors in the context of the code 
                and its previous analysis. Provide helpful hints for fixing them. DO NOT provide the complete solution, 
                only give hints that will help the student learn and understand how to fix the errors themselves.

                Focus on:
                1. Explaining the type of runtime error in simple terms
                2. Identifying potential causes based on the code structure
                3. Suggesting areas to check for common runtime issues:
                   - Memory access and allocation
                   - Array bounds
                   - Null pointer dereferences
                   - Division by zero
                   - Input handling
                4. Providing hints about debugging strategies
                5. Mentioning relevant C programming concepts to review
                6. Relating the error to the code structure and patterns identified in the analysis
                Provide the feedback withing 100 words.
                Remember: Provide only hints and guidance, not complete solutions.""",
                    ),
                    (
                        "human",
                        """Previous code analysis:
                {code_analysis}

                Code:
                {code}

                Runtime errors:
                {errors}

                Test input (if any):
                {input}""",
                    ),
                ]
            )

            if debug:
                print(
                    prompt.invoke(
                        {
                            "code": self.code_content,
                            "code_analysis": self.code_analysis,
                            "errors": runtime_errors,
                            "input": test_input if test_input else "No input provided",
                        }
                    )
                )

            chain = prompt | self.llm
            response = chain.invoke(
                {
                    "code": self.code_content,
                    "code_analysis": self.code_analysis,
                    "errors": runtime_errors,
                    "input": test_input if test_input else "No input provided",
                }
            )

            if debug:
                print("Runtime error analysis completed")
            return format_response(response.content)

        except Exception as e:
            if debug:
                print("Error in analyze_runtime_error:", str(e))
            return f"Error analyzing runtime errors: {str(e)}"

    def analyze_test_case_mismatch(
        self, test_input, actual_output, expected_output, debug=False
    ):
        """
        Analyze test case mismatch with context from the code analysis.

        Args:
            test_input (str): Input provided to the program
            actual_output (str): Output produced by the program
            expected_output (str): Expected output for the test case
            debug (bool): Whether to print debug information

        Returns:
            str: Hints for fixing the output mismatch
        """
        try:
            if debug:
                print("Analyzing test case mismatch")
                print("Test input:", test_input)
                print("Actual output:", actual_output)
                print("Expected output:", expected_output)

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """As a programming mentor, analyze the following test case mismatch in the context of the code 
                and its previous analysis. Provide helpful hints for fixing the output. DO NOT provide the complete solution, 
                only give hints that will help the student learn and understand how to fix the issue themselves.

                Focus on:
                1. Highlighting the key differences between actual and expected output
                2. Suggesting areas to check in the code based on the previous analysis
                3. Providing hints about potential logical issues
                4. Mentioning relevant programming concepts to review
                5. Relating the output mismatch to the code structure and patterns identified in the analysis
                Provide the feedback within 100 words.
                Remember: Provide only hints and guidance, not complete solutions.
                Provide only the feedback and nothing else.""",
                    ),
                    (
                        "human",
                        """Previous code analysis:
                {code_analysis}

                Code:
                {code}

                Test case details:
                Input: {input}
                Actual output: {actual}
                Expected output: {expected}""",
                    ),
                ]
            )

            if debug:
                print(
                    prompt.invoke(
                        {
                            "code": self.code_content,
                            "code_analysis": self.code_analysis,
                            "input": test_input,
                            "actual": actual_output,
                            "expected": expected_output,
                        }
                    )
                )

            chain = prompt | self.llm
            response = chain.invoke(
                {
                    "code": self.code_content,
                    "code_analysis": self.code_analysis,
                    "input": test_input,
                    "actual": actual_output,
                    "expected": expected_output,
                }
            )

            if debug:
                print("Test case mismatch analysis completed")
            return format_response(response.content)

        except Exception as e:
            if debug:
                print("Error in analyze_test_case_mismatch:", str(e))
            return f"Error analyzing test case mismatch: {str(e)}"


# Global analyzer instance
_analyzer = None


def get_analyzer():
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = CodeAnalyzer()
    return _analyzer


def get_code_feedback(filepath, debug=False):
    """
    Wrapper function to get code feedback and handle any errors.

    Args:
        filepath (str): Path to the C file to analyze
        debug (bool): Whether to print debug information

    Returns:
        dict: Dictionary containing feedback and status
    """
    # try:
    analyzer = get_analyzer()
    if debug:
        print("Analyzer loaded")
    if analyzer.load_code(filepath, debug):
        return {"status": "success", "feedback": analyzer.code_analysis}
    return {"status": "error", "feedback": analyzer.code_analysis}
    # except Exception as e:
    #     if debug:
    #         print("Error in get_code_feedback:", str(e))
    #     return {
    #         "status": "error",
    #         "feedback": f"Failed to analyze code: {str(e)}"
    #     }


def get_compilation_feedback(compile_errors, debug=False):
    """
    Wrapper function to get compilation error feedback.

    Args:
        compile_errors (str): Compilation error output from gcc
        debug (bool): Whether to print debug information

    Returns:
        dict: Dictionary containing feedback and status
    """
    try:
        analyzer = get_analyzer()
        if debug:
            print("Getting compilation feedback")
        feedback = analyzer.analyze_compilation_error(compile_errors, debug)
        return {"status": "success", "feedback": feedback}
    except Exception as e:
        if debug:
            print("Error in get_compilation_feedback:", str(e))
        return {
            "status": "error",
            "feedback": f"Failed to analyze compilation errors: {str(e)}",
        }


def get_runtime_feedback(runtime_errors, test_input=None, debug=False):
    """
    Wrapper function to get runtime error feedback.

    Args:
        runtime_errors (str): Runtime error output from the program
        test_input (str, optional): Input that caused the runtime error
        debug (bool): Whether to print debug information

    Returns:
        dict: Dictionary containing feedback and status
    """
    try:
        analyzer = get_analyzer()
        if debug:
            print("Getting runtime feedback")
        feedback = analyzer.analyze_runtime_error(runtime_errors, test_input, debug)
        return {"status": "success", "feedback": feedback}
    except Exception as e:
        if debug:
            print("Error in get_runtime_feedback:", str(e))
        return {
            "status": "error",
            "feedback": f"Failed to analyze runtime errors: {str(e)}",
        }


def get_test_case_feedback(test_input, actual_output, expected_output, debug=False):
    """
    Wrapper function to get test case mismatch feedback.

    Args:
        test_input (str): Input provided to the program
        actual_output (str): Output produced by the program
        expected_output (str): Expected output for the test case
        debug (bool): Whether to print debug information

    Returns:
        dict: Dictionary containing feedback and status
    """
    try:
        analyzer = get_analyzer()
        if debug:
            print("Getting test case feedback")
        feedback = analyzer.analyze_test_case_mismatch(
            test_input, actual_output, expected_output, debug
        )
        return {"status": "success", "feedback": feedback}
    except Exception as e:
        if debug:
            print("Error in get_test_case_feedback:", str(e))
        return {
            "status": "error",
            "feedback": f"Failed to analyze test case mismatch: {str(e)}",
        }
