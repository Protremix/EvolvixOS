#!/usr/bin/env python3
"""Intent Classifier — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        text = args.get("text", "").lower()
        if not text:
            return {"error": "text required"}
        intents = {
            "greeting": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy", "what's up"],
            "farewell": ["bye", "goodbye", "see you", "see ya", "later", "take care", "good night", "farewell"],
            "question": ["what", "how", "why", "when", "where", "who", "which", "is", "are", "can", "could", "would", "should", "do", "does"],
            "request": ["please", "could you", "would you", "can you", "help me", "i need", "i want", "get me", "show me", "find me"],
            "command": ["run", "execute", "start", "stop", "create", "delete", "update", "set", "install", "deploy", "build"],
            "gratitude": ["thanks", "thank you", "appreciate", "grateful", "thx"],
            "agreement": ["yes", "yeah", "sure", "ok", "okay", "correct", "right", "exactly", "agreed"],
            "disagreement": ["no", "nope", "wrong", "incorrect", "disagree", "not right", "not correct"],
            "apology": ["sorry", "apologize", "my bad", "excuse me", "forgive"],
            "emotion_positive": ["happy", "excited", "great", "awesome", "love", "wonderful", "amazing", "fantastic"],
            "emotion_negative": ["sad", "angry", "frustrated", "annoyed", "upset", "depressed", "worried", "stressed"],
            "schedule": ["schedule", "reminder", "meeting", "appointment", "calendar", "tomorrow", "today", "next week"],
            "search": ["find", "search", "look up", "google", "where is", "what is", "tell me about"],
            "code": ["code", "function", "class", "debug", "program", "script", "compile", "syntax", "variable", "loop"],
        }
        scores = {}
        for intent, keywords in intents.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[intent] = score
        detected = max(scores, key=scores.get) if scores else "unknown"
        return {"intent": detected, "confidence": round(scores[detected] / sum(scores.values()), 3) if scores else 0, "all_scores": scores}
