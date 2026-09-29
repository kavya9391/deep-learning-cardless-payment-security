# Create your views here.
from django.shortcuts import render, HttpResponse
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import UserRegistrationModel, TokenCountModel,TransactionModel, LoginOTPModel
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from datetime import datetime, timedelta
from jose import JWTError, jwt
import numpy as np
import os
import os

SECRET_KEY = "ce9941882f6e044f9809bcee90a2992b4d9d9c21235ab7c537ad56517050f26b"
ALGORITHM = "HS256"

import socket


def get_ipv4_address():
    try:
        # connect to an external host, doesn't send data
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google DNS
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return f"Error: {e}"


def create_access_token(data: dict):
    to_encode = data.copy()
    # expire time of the token
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # return the generated token
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HttpResponse(
            status_code=HttpResponse(status=204),
            detail="Could not validate credentials",
        )


# Create your views here.
def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            print('Data is Valid')

            # 1️⃣ Save user first
            user = form.save()

            # 2️⃣ Create token count using USER object
            TokenCountModel.objects.get_or_create(
                user=user,
                defaults={'count': 0}
            )

            # 3️⃣ Face capture
            from .utility import Model_tested
            Model_tested.capture_and_store_face(user.loginid)

            messages.success(request, 'You have been successfully registered')
            return render(request, 'UserRegistrations.html', {'form': UserRegistrationForm()})

        else:
            messages.success(request, 'Email or Mobile Already Existed')
            print("Invalid form")
    else:
        form = UserRegistrationForm()

    return render(request, 'UserRegistrations.html', {'form': form})


def UserLoginCheck(request):
    if request.method == "POST":
        email = request.POST.get('email')
        print("Email = ", email)
        try:
            check = UserRegistrationModel.objects.get(email=email)
            status = check.status
            print('Status is = ', status)
            if status == "activated":
                # Generate 6-digit OTP
                import random
                otp = str(random.randint(100000, 999999))

                # Delete old OTPs for this email
                LoginOTPModel.objects.filter(email=email).delete()

                # Save new OTP
                LoginOTPModel.objects.create(email=email, otp=otp)

                # Send OTP via email using Django's email system
                from django.core.mail import send_mail

                try:
                    subject = "Login OTP - Secure Financial Transactions"
                    message = f"""Hello {check.name},

Your OTP for login is: {otp}

This OTP is valid for 2 minutes only.

If you did not request this, please ignore this email.

Regards,
Secure Financial Transactions Team
"""

                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )

                    print(f"OTP sent successfully to {email}")

                    # Store email in session for OTP verification
                    request.session['login_email'] = email

                    return render(request, 'users/LoginOtpVerify.html', {})

                except Exception as email_error:
                    print(f"Email sending failed: {str(email_error)}")
                    messages.success(request, 'Failed to send OTP. Please try again.')
                    return render(request, 'UserLogin.html')
            else:
                messages.success(request, 'Your Account Not activated')
                return render(request, 'UserLogin.html')
        except Exception as e:
            print('Exception is ', str(e))
            pass
        messages.success(request, 'Email not registered')
    return render(request, 'UserLogin.html', {})


def UserHome(request):
    return render(request, 'users/UserHomePage.html', {'ip': get_ipv4_address()})


def user_transaction(request):
    if request.method == 'POST':
        sender_id = request.POST.get('sender_id')
        recipient_id = request.POST.get('recipient_id')
        amount = float(request.POST.get('amount'))
        remarks = request.POST.get('remarks')
        from .utility import Model_tested
        response = Model_tested.check_face_match()
        if response=='success':
            # 4. Generate OTP
            otp = Model_tested.generate_otp()
            print(f"Generated OTP: {otp}")
            # 5. Encrypt OTP
            encrypted_otp = Model_tested.encrypt(otp)
            print(f"Encrypted OTP: {encrypted_otp}")
            # 6. Decrypt OTP (Simulate system's decryption)
            decrypted_otp = Model_tested.decrypt(encrypted_otp)
            print(f"Decrypted OTP: {decrypted_otp}")

            # Send OTP to user's email
            from django.core.mail import send_mail
            user_email = request.session.get('email')
            user_name = request.session.get('loggeduser')

            try:
                subject = "Transaction OTP - Secure Financial Transactions"
                message = f"""Hello {user_name},

Your OTP for transaction is: {decrypted_otp}

Transaction Details:
- Amount: ${amount}
- Recipient: {recipient_id}
- Remarks: {remarks}

This OTP is valid for this transaction only.

If you did not initiate this transaction, please contact support immediately.

Regards,
Secure Financial Transactions Team
"""

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user_email],
                    fail_silently=False,
                )

                print(f"Transaction OTP sent successfully to {user_email}")

            except Exception as email_error:
                print(f"Email sending failed: {str(email_error)}")

            request.session['sender_id'] = sender_id
            request.session['recipient_id'] = recipient_id
            request.session['amount'] = amount
            request.session['remarks'] = remarks
            request.session['decrypted_otp'] = decrypted_otp
            return render(request, 'users/otpCheck.html', {})


        else:

            return render(request, 'users/faceNotMatch.html', {'msg': "Transaction failed: your face does not match"})

    else:
        loginid = request.session['loginid']
        from django.db.models import Q
        users = UserRegistrationModel.objects.filter(~Q(loginid=loginid))
        return render(request, 'users/send_money_form.html', {'loginid': loginid, 'users': users})

def userOtpVerify(request):
    brwOtp=request.POST.get('otpBrw')
    sender_id = request.session['sender_id']
    recipient_id = request.session['recipient_id']
    amount = request.session['amount']
    remarks = request.session['remarks']
    decrypted_otp = request.session['decrypted_otp']
    if decrypted_otp==brwOtp:
        import uuid
        transaction_id = str(uuid.uuid4())
        print("Transaction ID:", transaction_id)
        TransactionModel.objects.create(sender_id=sender_id,recipient_id=recipient_id,amount=amount,remarks=remarks,otp=decrypted_otp,transaction_id=transaction_id)
        from django.db.models import Q
        users = UserRegistrationModel.objects.filter(~Q(loginid=sender_id))
        return render(request, 'users/send_money_form.html',
                      {'loginid': sender_id, 'users': users, 'msg': f"Transaction Successful transaction id {transaction_id} "})

    else:
        from django.db.models import Q
        users = UserRegistrationModel.objects.filter(~Q(loginid=sender_id))
        return render(request, 'users/send_money_form.html', {'loginid': sender_id, 'users': users,'msg':"Transaction failed:your OTP wrong "})



from django.db.models import Q

def viewHistory(request):
    login_id = request.session.get('loginid')

    data = TransactionModel.objects.filter(
        Q(sender_id=login_id) | Q(recipient_id=login_id)
    )

    return render(request, 'users/viewHistory.html', {'data': data})


def LoginOtpVerify(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        email = request.session.get('login_email')

        if not email:
            messages.success(request, 'Session expired. Please login again.')
            return render(request, 'UserLogin.html')

        try:
            # Get the latest OTP for this email
            otp_record = LoginOTPModel.objects.filter(email=email).latest('created_at')

            # Check if OTP is expired (2 minutes)
            from datetime import timedelta
            from django.utils import timezone

            time_diff = timezone.now() - otp_record.created_at

            print(f"Current time: {timezone.now()}")
            print(f"OTP created at: {otp_record.created_at}")
            print(f"Time difference: {time_diff.total_seconds()} seconds")

            if time_diff > timedelta(minutes=2):
                LoginOTPModel.objects.filter(email=email).delete()
                messages.success(request, 'OTP expired. Please login again.')
                return render(request, 'UserLogin.html')

            # Verify OTP
            if otp_record.otp == entered_otp:
                # OTP is correct, complete login
                user = UserRegistrationModel.objects.get(email=email)

                request.session['id'] = user.id
                request.session['loggeduser'] = user.name
                request.session['loginid'] = user.loginid
                request.session['email'] = user.email

                data = {'loginid': user.loginid}
                token_jwt = create_access_token(data)
                request.session['token'] = token_jwt

                # Delete used OTP
                LoginOTPModel.objects.filter(email=email).delete()

                print(f"User {user.name} logged in successfully")
                return render(request, 'users/UserHomePage.html', {'ip': get_ipv4_address()})
            else:
                messages.success(request, 'Invalid OTP. Please try again.')
                return render(request, 'users/LoginOtpVerify.html')

        except LoginOTPModel.DoesNotExist:
            messages.success(request, 'OTP not found. Please login again.')
            return render(request, 'UserLogin.html')
        except Exception as e:
            print(f"Error in OTP verification: {str(e)}")
            messages.success(request, 'An error occurred. Please try again.')
            return render(request, 'UserLogin.html')

    return render(request, 'users/LoginOtpVerify.html')

