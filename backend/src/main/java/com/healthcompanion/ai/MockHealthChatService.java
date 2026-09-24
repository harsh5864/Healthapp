package com.healthcompanion.ai;

import com.healthcompanion.dto.ChatDtos.MessageResponse;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class MockHealthChatService implements HealthChatService {

    private static final String DISCLAIMER =
            "\n\n_Medical disclaimer: This information is for general educational purposes only and does not constitute medical advice or a diagnosis. Always consult a qualified healthcare professional._";

    private static final String EMERGENCY_NOTICE =
            "**[IMMEDIATE EMERGENCY ATTENTION RECOMMENDED]**\n\n" +
            "Your message mentions symptoms that may indicate a potentially life-threatening medical emergency. " +
            "Please seek emergency medical care immediately and call your local emergency service (e.g., 911/112/999) or proceed to the nearest emergency department. " +
            "Do not wait or drive yourself if you are feeling unwell." +
            DISCLAIMER;

    @Override
    public String respond(String text) {
        return respond(text, List.of());
    }

    @Override
    public String respond(String text, List<MessageResponse> history) {
        if (text == null || text.isBlank()) {
            return "Please provide a health question or symptom description so I can provide helpful information." + DISCLAIMER;
        }

        String t = text.toLowerCase();

        // 1. Red-flag emergency screening
        if (t.contains("chest pain") || t.contains("chest pressure") || t.contains("crushing chest") ||
            t.contains("difficulty breathing") || t.contains("shortness of breath") || t.contains("can't breathe") ||
            t.contains("passed out") || t.contains("lost consciousness") || t.contains("fainted") ||
            t.contains("slurred speech") || t.contains("facial droop") || t.contains("stroke") ||
            t.contains("allergic reaction") || t.contains("throat swelling") || t.contains("anaphylaxis") ||
            t.contains("uncontrolled bleeding") || t.contains("worst headache")) {
            return EMERGENCY_NOTICE;
        }

        // 2. Structured symptom domains
        if (t.contains("headache") || t.contains("migraine")) {
            return "[Development Mock Mode]\n\n" +
                   "**Regarding: Headache / Head discomfort**\n\n" +
                   "**1. What it could mean:**\n" +
                   "Headaches can be associated with tension, stress, dehydration, lack of sleep, eye strain, or sinus pressure.\n\n" +
                   "**2. Helpful questions to consider:**\n" +
                   "- Where is the pain located and how long has it lasted?\n" +
                   "- Did it begin gradually or suddenly?\n" +
                   "- Are you experiencing sensitivity to light or sound?\n\n" +
                   "**3. General supportive measures:**\n" +
                   "Resting in a quiet, dark room, staying hydrated, and avoiding prolonged screen time may help.\n\n" +
                   "**4. When to seek medical evaluation:**\n" +
                   "Seek professional care if the headache is sudden and unusually severe, or accompanied by stiff neck, fever, or confusion." +
                   DISCLAIMER;
        }

        if (t.contains("fever") || t.contains("temperature") || t.contains("chills")) {
            return "[Development Mock Mode]\n\n" +
                   "**Regarding: Fever / Elevated temperature**\n\n" +
                   "**1. What it could mean:**\n" +
                   "Fever is commonly the body's natural immune response to a viral or bacterial infection.\n\n" +
                   "**2. Helpful questions to consider:**\n" +
                   "- What is your current temperature reading and how many days has it persisted?\n" +
                   "- Do you have a cough, sore throat, or body aches?\n\n" +
                   "**3. General supportive measures:**\n" +
                   "Drink plenty of fluids (water, warm broth) and prioritize rest in a comfortable environment.\n\n" +
                   "**4. When to seek medical evaluation:**\n" +
                   "Consult a healthcare professional if fever exceeds 103°F (39.4°C), lasts more than three days, or occurs with a rash or breathing difficulty." +
                   DISCLAIMER;
        }

        if (t.contains("stomach") || t.contains("nausea") || t.contains("cramps") || t.contains("belly")) {
            return "[Development Mock Mode]\n\n" +
                   "**Regarding: Abdominal / Digestive discomfort**\n\n" +
                   "**1. What it could mean:**\n" +
                   "Abdominal discomfort can be associated with indigestion, dietary changes, viral gastroenteritis, or stress.\n\n" +
                   "**2. Helpful questions to consider:**\n" +
                   "- Is the pain sharp or cramping, and where is it located?\n" +
                   "- Have you noticed any nausea, vomiting, or changes in digestion?\n\n" +
                   "**3. General supportive measures:**\n" +
                   "Sip water or electrolyte fluids slowly and consume bland foods (crackers, rice) as tolerated.\n\n" +
                   "**4. When to seek medical evaluation:**\n" +
                   "Seek immediate care for severe or sudden localized pain, inability to keep fluids down, or blood in stool." +
                   DISCLAIMER;
        }

        return "[Development Mock Mode]\n\n" +
               "**Regarding: General Health Inquiry**\n\n" +
               "I can provide general, non-diagnostic educational information about health concerns.\n\n" +
               "**Helpful questions to consider:**\n" +
               "- When did you first notice these symptoms?\n" +
               "- What activities or factors make them feel better or worse?\n\n" +
               "**Recommended Next Steps:**\n" +
               "Keep track of when your symptoms happen and discuss any persistent or concerning symptoms with a doctor or healthcare professional." +
               DISCLAIMER;
    }
}
