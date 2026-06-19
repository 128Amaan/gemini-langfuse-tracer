import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langfuse import get_client, propagate_attributes

# load environment variables from the .env file
load_dotenv()

# initialize clients
langfuse_client = get_client()                                      # reads keys automatically from the environment
gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])  # the old google-generativeai package is deprecated; this is the current unified SDK

# store your prompt here
SYSTEM_PROMPT = """you are a helpful coding assistant. answer questions clearly and concisely. if you dont know something, tell it to me directly without guessing"""

MODEL = "gemini-2.5-flash"

# gemini's pricing (free tier = $0, but keeping cost tracking ready for when you upgrade)
# paid tier pricing per million tokens (input: $0.075, output: $0.30 for flash)
COST_PER_INPUT_TOKEN  = 0.075 / 1_000_000
COST_PER_OUTPUT_TOKEN = 0.30  / 1_000_000

LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")


def call_llm_with_tracing(
    user_message: str,
    session_id: str = "default-session",
    user_id: str = "anonymous"
) -> str:
    """
    Make a traced LLM call. Every call creates a langfuse trace with:
    -input and output
    -token usage(input,output,total)
    -calculated cost in USD
    -latency in milliseconds
    -model used and session context

    parameters:
        user_message: the message from the user
        session_id: groups related calls into one conversation
        user_id: mapping call with a user for analytics
    returns:
        The llm response as a string
    """

    # the root span becomes the "trace" in the Langfuse UI -- its input/output
    # are what show up at the trace level (this replaces the old trace.update())
    with langfuse_client.start_as_current_observation(
        as_type="span",
        name="coding support call",
        input={"user_message": user_message, "system_prompt": SYSTEM_PROMPT},
    ) as root_span:

        # propagate_attributes pushes session_id/user_id onto every observation
        # created inside this block (replaces session_id=/user_id= on trace())
        with propagate_attributes(session_id=session_id, user_id=user_id):

            # nested generation observation captures the model-specific details:
            # model name, tokens, cost (replaces trace.generation())
            with langfuse_client.start_as_current_observation(
                as_type="generation",
                name="gemini-completion",
                model=MODEL,
                input={
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}]
                },
            ) as generation:

                start_time = time.time()

                try:
                    # make the API call
                    response = gemini_client.models.generate_content(
                        model=MODEL,
                        contents=user_message,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT
                        )
                    )

                    latency_ms = int((time.time() - start_time) * 1000)

                    # extract the response text
                    response_text = response.text

                    # extract token usage from the response
                    input_tokens  = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count
                    total_tokens  = input_tokens + output_tokens

                    # calculate cost for this call
                    cost_usd = (
                        input_tokens  * COST_PER_INPUT_TOKEN +
                        output_tokens * COST_PER_OUTPUT_TOKEN
                    )

                    # update the generation with results (replaces generation.end())
                    generation.update(
                        output=response_text,
                        usage_details={
                            "input_tokens":  input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens":  total_tokens,
                        },
                        metadata={
                            "latency_ms": latency_ms,
                            "cost_usd":   round(cost_usd, 6),
                            "model":      MODEL
                        }
                    )

                    # update the root span -- this becomes the trace output
                    root_span.update(output={"response": response_text})

                    trace_id = langfuse_client.get_current_trace_id()

                    print(f"\n{'_'*60}")
                    print(f"user:    {user_message}")
                    print(f"gemini:  {response_text}")
                    print(f"tokens:  {input_tokens} in / {output_tokens} out / {total_tokens} total")
                    print(f"cost:    ${cost_usd:.6f}  (free tier = $0.00 charged)")
                    print(f"latency: {latency_ms}ms")
                    print(f"trace:   {LANGFUSE_HOST}/trace/{trace_id}")
                    print(f"{'_'*60}\n")

                    return response_text

                except Exception as e:
                    # record the error on the generation/span so it appears in langfuse
                    generation.update(
                        output=None,
                        metadata={"error": str(e), "latency_ms": int((time.time() - start_time) * 1000)}
                    )
                    root_span.update(output={"error": str(e)})

                    # always flush before raising -- ensures the error trace is sent
                    langfuse_client.flush()
                    raise

                finally:
                    # flush sends all buffered events to langfuse.
                    # in a long-running service, langfuse flushes automatically
                    # in a script, you must flush manually before the process exits
                    langfuse_client.flush()


# _____run a demonstration__________________________________
if __name__ == "__main__":
    # simulate 2 turns of the coding assistant conversation.
    test_messages = [
        "tell me the syntax to make a hashmap in java",
        "what is the space complexity of a code which uses a hashmap"
    ]

    session = "demo-session-001"

    for i, message in enumerate(test_messages):
        print(f"\nCall {i+1}/{len(test_messages)}")
        try:
            call_llm_with_tracing(
                user_message=message,
                session_id=session,
                user_id="test-user-42"
            )
        except Exception as e:
            print(f"error on call {i+1}: {e}")