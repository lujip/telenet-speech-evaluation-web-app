import json
import gc
from test_eval import run_full_evaluation

def parse_gpt_judgment(gpt_judgment):
    """Parse GPT judgment to extract comment and evaluation"""
    comment = None
    
    # Try to extract comment from gpt_judgment if it's a JSON string
    try:
        gpt_eval = json.loads(gpt_judgment) if isinstance(gpt_judgment, str) and gpt_judgment.strip().startswith('{') else None  # Parse JSON if possible
        if gpt_eval and 'comment' in gpt_eval:
            comment = gpt_eval['comment']  # Extract comment from parsed JSON
    except Exception:
        pass  # Ignore parsing errors
    
    if not comment:
        comment = gpt_judgment  # Use original judgment if no comment found
    
    return comment

def run_evaluation(question, keywords, audio_wav_path):
    """Run full evaluation and return parsed results"""
    result = run_full_evaluation(question, keywords, audio_wav_path)  # Run the complete evaluation process
    
    # Clean up memory
    gc.collect()  # Force garbage collection to free memory
    
    # Separate evaluation and comment
    evaluation = result.get("evaluation", {})  # Extract evaluation scores
    gpt_judgment = result.get("gpt_judgment", "")  # Get raw GPT response
    comment = parse_gpt_judgment(gpt_judgment)  # Parse comment from GPT response
    
    return {
        "transcript": result.get("transcript"),  # Return transcript of audio
        "audio_metrics": result.get("audio_metrics"),  # Return audio analysis metrics
        "evaluation": evaluation,  # Return parsed evaluation scores
        "comment": comment  # Return extracted comment
    } 