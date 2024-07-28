from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from yt_dlp import YoutubeDL
from django.conf import settings
import os
import assemblyai as aai
from .models import BlogPost
import google.generativeai as genai
from pytube.exceptions import RegexMatchError, VideoUnavailable


ASSEMBLYAI_API_KEY = 'e923464c9bc74edab43a336ddadb093d'
aai.settings.api_key = ASSEMBLYAI_API_KEY
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel('gemini-pro')



#client = OpenAI(api_key="sk-None-mvPOlRwkhvtdY5NsmV2NT3BlbkFJJ3l75BsIs4b9ay3kbhE0")
#sk-None-mvPOlRwkhvtdY5NsmV2NT3BlbkFJJ3l75BsIs4b9ay3kbhE0
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)

        title = yt_title(yt_link)
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': "Failed to get transcript"}, status=500)

        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': "Failed to generate blog article"}, status=500)

        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=yt_link,
            generated_content=blog_content,
            transcription=transcription  # Save the transcription text
        )
        new_blog_article.save()

        return JsonResponse({'content': blog_content, 'transcription': transcription})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def yt_title(link):
    ydl_opts = {
        'format': 'bestaudio/best',
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            return info_dict.get('title', 'Unknown Title')
    except Exception as e:
        return f"Error: {e}"

def download_audio(link):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link, download=True)
            if 'entries' in result:
                video = result['entries'][0]
            else:
                video = result
            filename = ydl.prepare_filename(video)
            audio_file = os.path.splitext(filename)[0] + '.mp3'
            return audio_file
    except Exception as e:
        print(f"Error: {e}")
        return None

# def get_transcription(link):
#     # Download audio file
#     audio_file = download_audio(link)
#     if not audio_file:
#         return None

#     # AssemblyAI transcription code
#     aai.settings.api_key = "e923464c9bc74edab43a336ddadb093d"
#     transcriber = aai.Transcriber()
#     transcript = transcriber.transcribe(audio_file)
#    return transcript.text


def get_transcription(link):
    audio_file = download_audio(link)
    if audio_file:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file)
        return transcript.text
    return None

#--------------------------**-----
def generate_blog_from_transcription(transcription):
    prompt = f"""
    Based on the following transcript from a YouTube video, write a comprehensive blog article. Write it based on the transcript, but don't make it look like it came from a YouTube video; make it look like a proper blog article. Use a single font style and avoid using bold text. Create significant space between paragraphs by adding <br><br> at the end of each paragraph:

    {transcription}

    Article:
    """
    try:
        response = model.generate_content(prompt)
        generated_content = response.candidates[0].content.parts[0].text.strip()

        # Replace double newlines with <br><br> for paragraph spacing
        formatted_content = generated_content.replace("\n\n", "<br><br>").replace("\n", " ")

        return formatted_content
    except Exception as e:
        print(f"API request error: {e}")
        return None




@login_required
def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

@login_required
def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail, 'transcription': blog_article_detail.transcription})
    else:
        return redirect('/')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Passwords do not match'
            return render(request, 'signup.html', {'error_message': error_message})

    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')
