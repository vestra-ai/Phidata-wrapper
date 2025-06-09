FIRESTORE_COLLECTIONS = {
    'USERS': 'users',
    'BATCHES': 'batches',
    'SYSTEMS': 'systems',
    'TOOLS': 'tools',
    'WAITLIST': 'waitlist',
    'PROMPTS': 'prompts',
    'UPLOADS': 'uploads',
    'AGENT_REQUESTS': 'agent_requests',
    'AFFILIATE_PROGRAMS': 'affiliate_programs',
    'X_PREDICTIONS': 'x_predictions',
    'GLOBAL_TASKS': 'global_tasks',
}

FIRESTORE_SUBCOLLECTIONS = {
    'USERS': {
        'REFERRALS': 'referrals',
        'TOKEN_HISTORY': 'token_history',
        'DECK': 'deck',
        'VAULT': 'vault',
    },
    'DECK': {
        'RUNS': 'runs',
    },
    'SYSTEMS': {
        'AGENTS': 'agents',
        'CONFIGS': 'configs',
        'COSTS': 'costs',
    },
    'AFFILIATE_PROGRAMS': {
        'PARTNERS': 'partners',
    },
}