# Render Deployment Guide

This guide will help you deploy the Face Recognition Attendance System on Render.

## Prerequisites

- A Render account (https://render.com)
- Git repository with your code
- The Dockerfile and render.yaml files included in this project

## Deployment Steps

### 1. Push to GitHub

Make sure your project is pushed to a GitHub repository:

```bash
git add .
git commit -m "Add Docker configuration for Render deployment"
git push origin main
```

### 2. Create a New Web Service on Render

1. Log in to your Render dashboard
2. Click **"New +"** and select **"Web Service"**
3. Connect your GitHub repository
4. Select the repository containing your attendance system

### 3. Configure the Web Service

**Basic Settings:**
- **Name**: attendance-system (or your preferred name)
- **Environment**: Docker
- **Region**: Choose the nearest region to your users
- **Branch**: main (or your deployment branch)

**Docker Settings:**
- **Dockerfile Path**: `./Dockerfile` (default)
- **Docker Context**: `./` (default)

**Environment Variables:**
- `PORT`: 5000
- `PYTHONUNBUFFERED`: 1

**Advanced Settings:**
- **Health Check Path**: `/api/students`
- **Auto-Deploy**: Yes (for automatic updates on push)

### 4. Add Persistent Disk (Optional but Recommended)

For data persistence:

1. Go to your service settings
2. Click **"Add Disk"**
3. Configure:
   - **Name**: attendance-data
   - **Size**: 1 GB (or more based on your needs)
   - **Mount Path**: `/app/ai-service`

### 5. Deploy

Click **"Create Web Service"** to start the deployment. Render will:
- Build the Docker image
- Install all dependencies
- Start your Flask application
- Run health checks

## Important Notes

### Database Persistence

The SQLite database (`attendance.db`) will be stored in the mounted disk to ensure data persistence across deployments.

### Face Recognition Dependencies

The Dockerfile includes all necessary system dependencies for:
- OpenCV
- face_recognition library
- Tesseract OCR
- dlib

### Performance Considerations

- **Free Tier**: The free tier has limited resources (512MB RAM, 0.5 CPU)
- **Face Recognition**: This is computationally intensive; consider upgrading to a paid plan for better performance
- **Concurrent Users**: Monitor performance and scale as needed

### Troubleshooting

**Build Issues:**
- Check the deployment logs on Render
- Ensure all dependencies are correctly specified in requirements.txt
- Verify the Dockerfile syntax

**Runtime Issues:**
- Check the service logs for errors
- Verify the health check endpoint is accessible
- Ensure the PORT environment variable is set correctly

**Performance Issues:**
- Monitor CPU and memory usage
- Consider upgrading to a paid plan for better resources
- Optimize face recognition algorithms if needed

## Environment Variables

You can customize the application with these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 5000 | Port the application listens on |
| FLASK_ENV | production | Flask environment (development/production) |
| PYTHONUNBUFFERED | 1 | Python output buffering |

## Scaling

For production use with multiple users:

1. **Upgrade Plan**: Move to a paid plan for more resources
2. **Load Balancing**: Render automatically handles load balancing
3. **Database**: Consider migrating to PostgreSQL for better scalability
4. **CDN**: Use Render's built-in CDN for static assets

## Security Considerations

- The application includes CORS support
- Consider adding authentication for production use
- Use HTTPS (Render provides this automatically)
- Regularly update dependencies

## Monitoring

Monitor your deployment using:
- Render's built-in metrics and logs
- Health check status
- Error rates and response times

## Support

If you encounter issues:
1. Check Render's documentation: https://render.com/docs
2. Review the deployment logs
3. Test locally using Docker: `docker build -t attendance . && docker run -p 5000:5000 attendance`
