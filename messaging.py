"""Draft-only outreach; this module never sends messages."""
def generate_message(lead,channel='WhatsApp',purpose='Initial outreach',sender=''):
    name=(lead.get('business_name') or 'your venue').strip(); sign=sender or 'ALOREX'
    if channel=='Email':
        if purpose=='Initial outreach': return f'Subject: A digital experience idea for {name}\n\nHello team,\n\nI’m building ALOREX, a digital experience layer for premium cafés and restaurants. I’d love to learn how {name} currently handles its guest-facing digital experience and see whether a tailored demo might be useful.\n\nWould you be open to a brief conversation?\n\nBest,\n{sign}'
        return f'Hello team,\n\nJust following up on my note about a possible digital guest-experience demo for {name}. If relevant, I’d be happy to arrange a short walkthrough. No worries if now isn’t a fit.\n\nBest,\n{sign}'
    if purpose=='Follow-up after reply': return f'Thanks for getting back to me. I’d be happy to learn more about {name} and show you a short, tailored ALOREX demo. What time would suit you?'
    if purpose=='No-response follow-up': return 'Hi! Just following up on my earlier message about ALOREX, a digital guest-experience layer for cafés and restaurants. If useful, I’d be happy to show you a short demo. Thanks!'
    if channel=='Instagram DM': return f'Hi! I’m building ALOREX, a digital guest-experience layer for premium cafés and restaurants. I’d love to learn a little about {name} and see if a tailored demo could be relevant. Would you be open to a quick chat?'
    return f'Hi! I’m building ALOREX, a digital guest-experience layer for cafés and restaurants. I’d love to learn how {name} handles its guest experience and, if relevant, show you a short tailored demo. Would you be open to a quick chat?'
