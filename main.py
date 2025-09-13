from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import auth, users, doctors, appointments, payments, chatbot, password_routes, file_upload


# FastAPI app
app = FastAPI(title="Doctor Appointment Booking System")

# CORS for frontend
origins = [
    "http://localhost:3000",   # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:3001",   # Next.js dev server
    "http://127.0.0.1:3001",
    "https://docassist-web.vercel.app"  # <-- deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(payments.router)
app.include_router(chatbot.router)
app.include_router(password_routes.router)
app.include_router(file_upload.router)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def root():
    return {"message": "Doctor Appointment Booking System API is running 🚀"}
