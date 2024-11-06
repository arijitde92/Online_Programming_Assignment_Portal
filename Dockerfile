FROM python:3.11-alpine

# Set up environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY="abcd1234"
ENV SQLALCHEMY_DATABASE_URI="mysql+mysqlconnector://avnadmin:AVNS_LF2LhgmUdSoMWNcGWhI@mysql-assignment-evaluator-assignment-evaluator.b.aivencloud.com:19148/assignment_evaluator"
ENV SQLALCHEMY_TRACK_MODIFICATIONS="False"

# Create and set the working directory
WORKDIR /app

# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Expose the port your application will run on
EXPOSE 6500

# Specify the command to run on container start
CMD ["python", "src/app.py"]