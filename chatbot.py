"""
Testiny Equipments AI Chatbot Module
Integrates with Ollama (LLaMA model) for industrial equipment Q&A.
Includes fallback responses when Ollama is not available.
"""

import requests
import json

# System prompt that gives the AI context about Teslead
SYSTEM_PROMPT = """You are the AI assistant for Testiny Equipments Private Limited, an industrial company 
specializing in manufacturing and supplying:

1. **Test Equipment**: Pump Test Rigs, Valve Test Benches, Pressure Testing Systems
2. **Hydraulic Systems**: Hydraulic Power Packs (1-500 HP), Hydraulic Cylinders (25-500mm bore), Pressure Boosters (up to 2500 bar)
3. **Pneumatic Systems**: Pneumatic Control Systems, Air Preparation Units (FRL)
4. **Special Machines**: Custom SPMs, Industrial Flushing Rigs

Key Facts:
- We serve Oil & Gas, Automobile, Power Plants, and Manufacturing industries
- Our test rigs comply with API, ISO, ASME, and EN standards
- We provide custom-engineered solutions with PLC automation and HMI interfaces
- Hydraulic systems range from 1 HP to 500 HP power packs
- Pressure testing capabilities up to 2000 bar
- We provide complete turnkey solutions including design, manufacturing, installation, and commissioning

You should answer questions about:
- Product specifications and capabilities
- Working principles of hydraulic, pneumatic, and testing systems
- Differences between hydraulic and pneumatic systems
- Product recommendations based on application requirements
- General industrial engineering concepts related to our products

Be professional, knowledgeable, and helpful. Provide technical details when asked.
Keep responses concise but informative. If asked about pricing, direct them to the contact/enquiry page.
"""

# Fallback responses for when Ollama is not available
FALLBACK_RESPONSES = {
    "hydraulic power pack": (
        "A **Hydraulic Power Pack** is a self-contained unit that generates hydraulic power. It consists of:\n\n"
        "• **Electric Motor**: Drives the hydraulic pump (1 HP to 500 HP)\n"
        "• **Hydraulic Pump**: Converts mechanical energy to hydraulic energy (Gear, Vane, or Piston type)\n"
        "• **Reservoir**: Stores hydraulic fluid (10L to 5000L)\n"
        "• **Valve Manifold**: Controls direction, pressure, and flow\n"
        "• **Filtration**: Keeps fluid clean (10μm return, 3μm pressure line)\n"
        "• **Cooling System**: Air-cooled or water-cooled heat exchangers\n\n"
        "Operating pressures up to 350 bar. Used in machine tools, steel mills, marine applications, and industrial automation."
    ),
    "pump test rig": (
        "A **Pump Test Rig** is used to evaluate pump performance by measuring:\n\n"
        "• Flow rate (0.5 - 5000 LPM)\n"
        "• Discharge pressure (0 - 500 bar)\n"
        "• Input torque and power consumption\n"
        "• Efficiency at various operating points\n\n"
        "Our test rigs feature PLC-based data acquisition, variable speed drives, and can test centrifugal, "
        "gear, vane, and piston pumps. Used by pump manufacturers, oil & gas companies, and power plants."
    ),
    "valve test bench": (
        "A **Valve Test Bench** performs hydrostatic and pneumatic testing of valves per API 598 / ISO 5208 standards.\n\n"
        "• Test pressure up to 1000 bar (hydrostatic)\n"
        "• Pneumatic seat leakage testing up to 50 bar\n"
        "• Valve sizes from DN15 to DN600\n"
        "• Automated test sequences with digital certificate generation\n"
        "• Universal hydraulic clamping system\n\n"
        "Used by valve manufacturers, refineries, and power plants for production testing and recertification."
    ),
    "pneumatic": (
        "**Pneumatic Systems** use compressed air as the working medium.\n\n"
        "**Advantages over Hydraulic:**\n"
        "• Cleaner operation (air vs oil)\n"
        "• Faster actuator speeds\n"
        "• Lower cost for light-duty applications\n"
        "• Simpler maintenance\n\n"
        "**Limitations:**\n"
        "• Lower force output (typically 0-10 bar vs 0-350 bar)\n"
        "• Less precise speed control (air is compressible)\n"
        "• Not suitable for heavy loads\n\n"
        "We offer pneumatic control valves (3/2, 5/2, 5/3 way), FRL units, and complete control systems."
    ),
    "hydraulic vs pneumatic": (
        "**Hydraulic vs Pneumatic Systems Comparison:**\n\n"
        "| Feature | Hydraulic | Pneumatic |\n"
        "|---------|-----------|----------|\n"
        "| Medium | Oil | Compressed Air |\n"
        "| Pressure | Up to 350 bar | Up to 10 bar |\n"
        "| Force | Very High | Moderate |\n"
        "| Speed | Moderate | Fast |\n"
        "| Precision | Excellent | Good |\n"
        "| Cost | Higher | Lower |\n"
        "| Cleanliness | Oil leaks possible | Clean |\n"
        "| Compressibility | Incompressible | Compressible |\n\n"
        "**Choose Hydraulic** for: heavy loads, precise positioning, high force\n"
        "**Choose Pneumatic** for: fast cycling, clean environments, light loads"
    ),
    "oil pump": (
        "For testing oil pumps, we recommend our **Pump Test Rig** which can handle:\n\n"
        "• Flow rates: 0.5 - 5000 LPM\n"
        "• Pressure: Up to 500 bar\n"
        "• Test medium: Hydraulic oil, water, or custom fluids\n"
        "• Variable speed drive for performance curve generation\n\n"
        "The rig generates complete pump performance curves including Head vs Flow, Efficiency vs Flow, "
        "and Power vs Flow characteristics. Ideal for R&D, quality assurance, and type testing."
    ),
    "default": (
        "Thank you for your question! I'm the Testiny Equipments AI assistant.\n\n"
        "I can help you with information about:\n"
        "• **Test Equipment** — Pump Test Rigs, Valve Test Benches, Pressure Testing Systems\n"
        "• **Hydraulic Systems** — Power Packs, Cylinders, Boosters\n"
        "• **Pneumatic Systems** — Control Valves, Air Preparation Units\n"
        "• **Special Machines** — Custom SPMs, Flushing Rigs\n\n"
        "Try asking:\n"
        "- \"What is a hydraulic power pack?\"\n"
        "- \"Which test rig is used for oil pumps?\"\n"
        "- \"Difference between pneumatic and hydraulic system?\"\n\n"
        "For pricing and custom requirements, please visit our **Contact** page to submit an enquiry."
    )
}


def get_chat_response(query, ollama_base_url='http://localhost:11434', model='llama3'):
    """
    Send a query to Ollama and return the AI response.
    Falls back to predefined responses if Ollama is unavailable.
    
    Args:
        query: User's question string
        ollama_base_url: Ollama API base URL
        model: LLaMA model name
    
    Returns:
        dict: {'response': str, 'source': 'ollama'|'fallback'}
    """
    # First, try Ollama
    try:
        print(f'[Chatbot] Calling Ollama at {ollama_base_url}/api/chat with model={model}')
        response = requests.post(
            f'{ollama_base_url}/api/chat',
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': query}
                ],
                'stream': False
            },
            timeout=120  # LLaMA needs time to load on first call
        )

        print(f'[Chatbot] Ollama response status: {response.status_code}')

        if response.status_code == 200:
            data = response.json()
            ai_response = data.get('message', {}).get('content', '')
            if ai_response:
                print(f'[Chatbot] Got Ollama response ({len(ai_response)} chars)')
                return {'response': ai_response, 'source': 'ollama'}
            else:
                print(f'[Chatbot] Empty response from Ollama: {data}')
        else:
            print(f'[Chatbot] Ollama error: {response.text}')

    except requests.Timeout:
        print('[Chatbot] Ollama timed out (120s)')
    except requests.ConnectionError:
        print('[Chatbot] Cannot connect to Ollama - is it running?')
    except Exception as e:
        print(f'[Chatbot] Unexpected error: {type(e).__name__}: {e}')

    # Fallback: match keywords in query
    print('[Chatbot] Using fallback response')
    return {'response': get_fallback_response(query), 'source': 'fallback'}


def get_fallback_response(query):
    """
    Return a pre-built response based on keyword matching.
    Used when Ollama is not available.
    """
    query_lower = query.lower()

    # Check for specific keyword matches
    if 'hydraulic' in query_lower and 'pneumatic' in query_lower:
        return FALLBACK_RESPONSES['hydraulic vs pneumatic']
    if 'hydraulic' in query_lower and ('power pack' in query_lower or 'powerpack' in query_lower):
        return FALLBACK_RESPONSES['hydraulic power pack']
    if 'pump' in query_lower and ('test' in query_lower or 'rig' in query_lower):
        return FALLBACK_RESPONSES['pump test rig']
    if 'valve' in query_lower and ('test' in query_lower or 'bench' in query_lower):
        return FALLBACK_RESPONSES['valve test bench']
    if 'pneumatic' in query_lower:
        return FALLBACK_RESPONSES['pneumatic']
    if 'oil' in query_lower and 'pump' in query_lower:
        return FALLBACK_RESPONSES['oil pump']
    if 'hydraulic' in query_lower:
        return FALLBACK_RESPONSES['hydraulic power pack']

    return FALLBACK_RESPONSES['default']
