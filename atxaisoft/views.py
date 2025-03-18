# from django.shortcuts import render
# import google.generativeai as genai
# import speech_recognition as sr
# from gtts import gTTS
# from django.http import JsonResponse
# import io
# import base64

# def speech_to_text(request):
#     """Konuşmayı metne çevir ve AI yanıtını sesli olarak döndür"""
#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         recognizer.adjust_for_ambient_noise(source)
#         print("Konuşmayı dinliyorum...")
#         audio = recognizer.listen(source)

#     try:
#         user_text = recognizer.recognize_google(audio, language="tr-TR")

#         # === AI Modelinden Yanıt Al ===
#         genai.configure(api_key="AIzaSyCAXB_dpcnWNSmyQYtrnwh1dopd_wFUP20")
#         model = genai.GenerativeModel(model_name="gemini-1.5-flash")
#         response = model.generate_content(user_text)
#         ai_response = response.text

#         # === Yanıtı Seslendirme (Text-to-Speech) ===
#         tts = gTTS(text=ai_response, lang="tr")
#         mp3_fp = io.BytesIO()
#         tts.write_to_fp(mp3_fp)
#         mp3_fp.seek(0)

#         # MP3'ü Base64'e çevir
#         audio_base64 = base64.b64encode(mp3_fp.read()).decode("utf-8")

#         return JsonResponse({"text": ai_response, "audio": audio_base64})
    
#     except sr.UnknownValueError:
#         return JsonResponse({"error": "Ses anlaşılamadı."})
#     except sr.RequestError:
#         return JsonResponse({"error": "Google servislerine erişilemiyor."})

# def home(request):
#     """Ana sayfa render edilir"""
#     return render(request, "voice_assistant.html")


from django.shortcuts import render
import google.generativeai as genai
import sounddevice as sd
import numpy as np
import queue
import io
import base64
from gtts import gTTS
from django.http import JsonResponse
import speech_recognition as sr
import soundfile as sf


def text_to_speech(ai_response, audio_queue):
    """AI yanıtını ses dosyasına çevir ve Base64 olarak kuyruğa ekle"""
    tts = gTTS(text=ai_response, lang="tr")
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    audio_base64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
    audio_queue.put(audio_base64)


def record_audio(duration=5, samplerate=16000):
    """Mikrofondan ses kaydı yap ve WAV formatında döndür"""
    q = queue.Queue()
    
    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(indata.copy())

    with sd.InputStream(samplerate=samplerate, channels=1, callback=callback):
        print("Konuşmayı dinliyorum...")
        audio_data = []
        for _ in range(0, int(samplerate / 1024 * duration)):
            audio_data.append(q.get())

    audio_np = np.concatenate(audio_data, axis=0)
    audio_wav = io.BytesIO()
    
    # WAV formatında kaydet
    sf.write(audio_wav, audio_np, samplerate, format='WAV')
    audio_wav.seek(0)

    return audio_wav


def speech_to_text(request):
    """Konuşmayı metne çevir ve AI yanıtını asenkron sesli olarak döndür"""
    recognizer = sr.Recognizer()
    audio_wav = record_audio()
    
    with sr.AudioFile(audio_wav) as source:
        audio = recognizer.record(source)
    
    try:
        user_text = recognizer.recognize_google(audio, language="tr-TR")

        # === AI Modelinden Yanıt Al ===
        genai.configure(api_key="AIzaSyCAXB_dpcnWNSmyQYtrnwh1dopd_wFUP20")  # API anahtarınızı buraya ekleyin.
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(user_text)
        ai_response = response.text

        # === Yanıtı Asenkron Olarak Seslendirme (Text-to-Speech) ===
        audio_queue = queue.Queue()
        text_to_speech(ai_response, audio_queue)
        audio_base64 = audio_queue.get()

        return JsonResponse({"text": ai_response, "audio": audio_base64})

    except sr.UnknownValueError:
        return JsonResponse({"error": "Ses anlaşılamadı."})
    except sr.RequestError:
        return JsonResponse({"error": "Google servislerine erişilemiyor."})

def home(request):
    """Ana sayfa render edilir"""
    return render(request, "voice_assistant.html")

def chat(request):
    """chat sayfa render edilir"""
    return render(request, "footer.html")
