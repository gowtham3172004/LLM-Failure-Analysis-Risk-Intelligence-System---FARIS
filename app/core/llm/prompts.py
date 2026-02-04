"""
FARIS Prompt Templates

Carefully engineered prompts for each failure detector and analysis node.
All prompts are designed to produce structured, parseable outputs.
"""


class PromptTemplates:
    """
    Centralized prompt templates for FARIS analysis.
    
    Design principles:
    - Request structured JSON output
    - Include clear examples
    - Define explicit output schemas
    - Minimize hallucination by being specific
    """
    
    # =========================================================================
    # SYSTEM PROMPTS
    # =========================================================================
    
    ANALYZER_SYSTEM = """You are FARIS, an expert AI system that analyzes LLM outputs for potential failures.
Your role is to identify problems in AI-generated answers, NOT to generate answers yourself.
You must be precise, evidence-based, and never make unsupported claims.
Always respond with valid JSON in the exact format requested."""
    
    CRITIC_SYSTEM = """You are a critical analyst examining LLM outputs for reliability issues.
You look for logical flaws, unsupported claims, and potential failures.
Be thorough but fair - only flag genuine issues with clear evidence.
Always respond with valid JSON."""
    
    # =========================================================================
    # CLAIM DECOMPOSITION
    # =========================================================================
    
    DECOMPOSE_CLAIMS = """Analyze the following LLM answer and extract all distinct claims made.

QUESTION: {question}

LLM ANSWER: {answer}

CONTEXT (if provided): {context}

For each claim, identify:
1. The atomic statement being made
2. Whether it's a factual claim, opinion, or reasoning step
3. Any implicit assumptions required for the claim to be true

Respond with JSON in this exact format:
{{
    "claims": [
        {{
            "claim_id": "c1",
            "claim_text": "The specific claim text",
            "claim_type": "factual|opinion|reasoning",
            "implicit_assumptions": ["assumption 1", "assumption 2"]
        }}
    ],
    "overall_assumptions": ["List of assumptions the entire answer depends on"],
    "reasoning_chain": ["Step 1", "Step 2"] 
}}

Extract ALL claims, even seemingly obvious ones. Be thorough."""
    
    # =========================================================================
    # HALLUCINATION DETECTION
    # =========================================================================
    
    DETECT_HALLUCINATION = """Analyze the following claims for potential hallucinations.

ORIGINAL QUESTION: {question}

CONTEXT PROVIDED: {context}

CLAIMS TO ANALYZE:
{claims}

For each claim, determine if it contains hallucination - information that is:
- Not supported by the provided context
- Fabricated facts, numbers, or citations
- Made-up entities, people, or events
- Incorrect technical details

Respond with JSON:
{{
    "hallucination_detected": true|false,
    "confidence": 0.0-1.0,
    "severity": "low|medium|high|critical",
    "findings": [
        {{
            "claim_id": "c1",
            "is_hallucinated": true|false,
            "confidence": 0.0-1.0,
            "reason": "Explanation of why this is/isn't hallucinated",
            "evidence": "What evidence supports this finding"
        }}
    ],
    "summary": "Brief summary of hallucination analysis"
}}

Be conservative - only flag clear hallucinations with high confidence."""
    
    # =========================================================================
    # LOGICAL INCONSISTENCY DETECTION
    # =========================================================================
    
    DETECT_LOGICAL_INCONSISTENCY = """Analyze the following answer for logical inconsistencies.

QUESTION: {question}

ANSWER: {answer}

EXTRACTED CLAIMS:
{claims}

REASONING CHAIN:
{reasoning_chain}

Look for:
1. Internal contradictions (claim A contradicts claim B)
2. Non sequiturs (conclusions that don't follow from premises)
3. Invalid inference patterns
4. Circular reasoning
5. Missing logical steps

Respond with JSON:
{{
    "inconsistency_detected": true|false,
    "confidence": 0.0-1.0,
    "severity": "low|medium|high|critical",
    "findings": [
        {{
            "type": "contradiction|non_sequitur|invalid_inference|circular|missing_step",
            "description": "What the inconsistency is",
            "involved_claims": ["c1", "c2"],
            "explanation": "Why this is a logical problem"
        }}
    ],
    "summary": "Brief summary of logical analysis"
}}"""
    
    # =========================================================================
    # MISSING ASSUMPTIONS DETECTION
    # =========================================================================
    
    DETECT_MISSING_ASSUMPTIONS = """Analyze whether the answer makes unstated assumptions that should be explicit.

QUESTION: {question}

CONTEXT: {context}

ANSWER: {answer}

IDENTIFIED ASSUMPTIONS:
{assumptions}

Check if:
1. The answer assumes conditions not stated in the question
2. Critical context is assumed but not verified
3. Domain-specific knowledge is assumed without acknowledgment
4. Edge cases or exceptions are ignored
5. Temporal or situational assumptions are made

Respond with JSON:
{{
    "missing_assumptions_detected": true|false,
    "confidence": 0.0-1.0,
    "severity": "low|medium|high|critical",
    "findings": [
        {{
            "assumption": "What is being assumed",
            "impact": "How this affects the answer's validity",
            "should_be_stated": true|false,
            "suggested_clarification": "How to make this explicit"
        }}
    ],
    "summary": "Brief summary of assumption analysis"
}}"""
    
    # =========================================================================
    # OVERCONFIDENCE DETECTION
    # =========================================================================
    
    DETECT_OVERCONFIDENCE = """Analyze the answer for overconfident language that isn't warranted.

QUESTION: {question}

ANSWER: {answer}

CLAIMS:
{claims}

Look for:
1. Absolute language ("always", "never", "definitely", "certainly")
2. Lack of uncertainty acknowledgment where appropriate
3. Definitive statements on uncertain topics
4. Missing caveats or qualifications
5. Tone vs. evidence mismatch

Respond with JSON:
{{
    "overconfidence_detected": true|false,
    "confidence": 0.0-1.0,
    "severity": "low|medium|high|critical",
    "findings": [
        {{
            "text": "The overconfident statement",
            "claim_id": "c1",
            "issue": "Why this is overconfident",
            "suggested_revision": "A more appropriately hedged version"
        }}
    ],
    "absolute_terms_found": ["list", "of", "absolute", "terms"],
    "summary": "Brief summary of overconfidence analysis"
}}"""
    
    # =========================================================================
    # SCOPE VIOLATION DETECTION
    # =========================================================================
    
    DETECT_SCOPE_VIOLATION = """Analyze whether the answer stays within the scope of the question.

QUESTION: {question}

ANSWER: {answer}

Check for:
1. Information beyond what was asked
2. Tangential topics introduced
3. Unsolicited advice or opinions
4. Scope creep from the original question
5. Relevant but unnecessary elaboration

Respond with JSON:
{{
    "scope_violation_detected": true|false,
    "confidence": 0.0-1.0,
    "severity": "low|medium|high|critical",
    "findings": [
        {{
            "text": "The out-of-scope content",
            "violation_type": "tangent|unsolicited|elaboration|different_topic",
            "explanation": "Why this is out of scope"
        }}
    ],
    "summary": "Brief summary of scope analysis"
}}"""
    
    # =========================================================================
    # UNDERSPECIFICATION DETECTION
    # =========================================================================
    
    DETECT_UNDERSPECIFICATION = """Analyze whether the question lacks necessary information for a reliable answer.

QUESTION: {question}

CONTEXT: {context}

ANSWER: {answer}

Check if:
1. The question is ambiguous
2. Critical parameters are missing
3. Multiple valid interpretations exist
4. The answer should have asked for clarification
5. Assumptions were made that should have been questions

Respond with JSON:
{{
    "underspecification_detected": true|false,
    "confidence": 0.0-1.0,
    "severity": "low|medium|high|critical",
    "findings": [
        {{
            "issue": "What information is missing",
            "ambiguity_type": "parameter|scope|interpretation|context",
            "possible_interpretations": ["interp1", "interp2"],
            "should_clarify": true|false
        }}
    ],
    "clarifying_questions": ["Questions that should have been asked"],
    "summary": "Brief summary of underspecification analysis"
}}"""
    
    # =========================================================================
    # EXPLANATION GENERATION
    # =========================================================================
    
    GENERATE_EXPLANATION = """Generate a clear, structured explanation of the failure analysis results.

QUESTION: {question}

ANSWER: {answer}

DETECTED FAILURES:
{failures}

CLAIMS ANALYSIS:
{claims}

RISK SCORE: {risk_score}
RISK LEVEL: {risk_level}

Generate a human-readable explanation that:
1. Summarizes the key findings
2. Explains why each failure matters
3. Connects failures to specific claims
4. Is clear to developers who need to fix issues

Respond with JSON:
{{
    "summary": "One paragraph executive summary",
    "key_findings": [
        "Finding 1 in plain language",
        "Finding 2 in plain language"
    ],
    "detailed_explanation": "Multi-paragraph detailed explanation",
    "impact_assessment": "How these failures could affect users"
}}"""
    
    # =========================================================================
    # RECOMMENDATION GENERATION
    # =========================================================================
    
    GENERATE_RECOMMENDATIONS = """Generate actionable recommendations to address the detected failures.

DETECTED FAILURES:
{failures}

DOMAIN: {domain}

For each failure type, provide specific, actionable recommendations.

Respond with JSON:
{{
    "recommendations": [
        {{
            "recommendation_id": "r1",
            "priority": 1-5,
            "failure_type": "the failure type this addresses",
            "title": "Short action title",
            "description": "Detailed description of what to do",
            "implementation_hint": "Technical guidance for implementation"
        }}
    ]
}}

Prioritize recommendations by impact and feasibility.
Priority 1 = most urgent, Priority 5 = nice to have."""
    
    # =========================================================================
    # PRECHECK
    # =========================================================================
    
    PRECHECK_INPUT = """Analyze the following input for quality and suitability for failure analysis.

QUESTION: {question}

LLM ANSWER: {answer}

Check for:
1. Is the answer actually an attempt to answer the question?
2. Is it a refusal or error message?
3. Is there enough content to analyze?
4. Is the content coherent text (not gibberish)?

Respond with JSON:
{{
    "is_valid": true|false,
    "issues": ["list of issues if not valid"],
    "answer_type": "response|refusal|error|empty|gibberish",
    "proceed_with_analysis": true|false,
    "reason": "Brief explanation"
}}"""
