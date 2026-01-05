"""Resume file operations for applicant resume uploads and management"""

import os
import shutil
from datetime import datetime
from config import RESUME_DIR
from werkzeug.utils import secure_filename

# Allowed file extensions for resumes
ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB


def ensure_resume_directory():
    """Ensure the resume directory exists"""
    if not os.path.exists(RESUME_DIR):
        os.makedirs(RESUME_DIR)
        print(f"✓ Created resume directory: {RESUME_DIR}")


def allowed_resume_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS


def get_file_extension(filename):
    """Get the file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def save_applicant_resume(file, applicant_id):
    """
    Save an applicant's resume file
    
    Args:
        file: File object from request
        applicant_id: ID of the applicant
        
    Returns:
        dict: {success: bool, message: str, filename: str, path: str}
    """
    try:
        ensure_resume_directory()
        
        # Validate file
        if not file or file.filename == '':
            return {
                'success': False,
                'message': 'No file selected',
                'filename': None,
                'path': None
            }
        
        if not allowed_resume_file(file.filename):
            return {
                'success': False,
                'message': f'Invalid file type. Allowed types: {", ".join(ALLOWED_RESUME_EXTENSIONS)}',
                'filename': None,
                'path': None
            }
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_RESUME_SIZE:
            return {
                'success': False,
                'message': f'File size exceeds maximum of {MAX_RESUME_SIZE / (1024*1024):.0f} MB',
                'filename': None,
                'path': None
            }
        
        # Create applicant-specific directory
        applicant_resume_dir = os.path.join(RESUME_DIR, applicant_id)
        if not os.path.exists(applicant_resume_dir):
            os.makedirs(applicant_resume_dir)
        
        # Generate secure filename
        original_filename = secure_filename(file.filename)
        file_extension = get_file_extension(original_filename)
        
        # Create filename with timestamp to avoid overwrites
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"resume_{timestamp}.{file_extension}"
        
        # Save file
        filepath = os.path.join(applicant_resume_dir, filename)
        file.save(filepath)
        
        # Return relative path (just applicant_id/filename, without 'resume/' prefix)
        relative_path = f"{applicant_id}/{filename}"
        
        return {
            'success': True,
            'message': 'Resume uploaded successfully',
            'filename': filename,
            'path': relative_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error uploading resume: {str(e)}',
            'filename': None,
            'path': None
        }


def get_applicant_resume(applicant_id):
    """
    Get the latest resume file for an applicant
    
    Args:
        applicant_id: ID of the applicant
        
    Returns:
        dict: {success: bool, filename: str, path: str, message: str}
    """
    try:
        applicant_resume_dir = os.path.join(RESUME_DIR, applicant_id)
        
        if not os.path.exists(applicant_resume_dir):
            return {
                'success': False,
                'filename': None,
                'path': None,
                'message': 'No resume found for this applicant'
            }
        
        # Get list of resume files, sorted by modification time (latest first)
        files = [f for f in os.listdir(applicant_resume_dir) if os.path.isfile(os.path.join(applicant_resume_dir, f))]
        
        if not files:
            return {
                'success': False,
                'filename': None,
                'path': None,
                'message': 'No resume found for this applicant'
            }
        
        # Get the latest file
        files.sort(key=lambda f: os.path.getmtime(os.path.join(applicant_resume_dir, f)), reverse=True)
        latest_filename = files[0]
        
        relative_path = f"{applicant_id}/{latest_filename}"
        
        return {
            'success': True,
            'filename': latest_filename,
            'path': relative_path,
            'message': 'Resume found'
        }
        
    except Exception as e:
        return {
            'success': False,
            'filename': None,
            'path': None,
            'message': f'Error retrieving resume: {str(e)}'
        }


def delete_applicant_resume(applicant_id, filename=None):
    """
    Delete an applicant's resume file(s)
    
    Args:
        applicant_id: ID of the applicant
        filename: Optional specific filename to delete. If None, deletes all
        
    Returns:
        dict: {success: bool, message: str}
    """
    try:
        applicant_resume_dir = os.path.join(RESUME_DIR, applicant_id)
        
        if not os.path.exists(applicant_resume_dir):
            return {
                'success': False,
                'message': 'Resume directory not found'
            }
        
        if filename:
            # Delete specific file
            filepath = os.path.join(applicant_resume_dir, secure_filename(filename))
            if os.path.exists(filepath):
                os.remove(filepath)
                return {
                    'success': True,
                    'message': 'Resume file deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Resume file not found'
                }
        else:
            # Delete entire applicant resume directory
            if os.path.exists(applicant_resume_dir):
                shutil.rmtree(applicant_resume_dir)
            return {
                'success': True,
                'message': 'All resume files deleted successfully'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Error deleting resume: {str(e)}'
        }


def get_applicant_all_resumes(applicant_id):
    """
    Get all resume files for an applicant
    
    Args:
        applicant_id: ID of the applicant
        
    Returns:
        dict: {success: bool, resumes: list, message: str}
    """
    try:
        applicant_resume_dir = os.path.join(RESUME_DIR, applicant_id)
        
        if not os.path.exists(applicant_resume_dir):
            return {
                'success': False,
                'resumes': [],
                'message': 'No resume directory found'
            }
        
        files = [f for f in os.listdir(applicant_resume_dir) if os.path.isfile(os.path.join(applicant_resume_dir, f))]
        
        if not files:
            return {
                'success': False,
                'resumes': [],
                'message': 'No resumes found'
            }
        
        # Sort by modification time (latest first)
        files.sort(key=lambda f: os.path.getmtime(os.path.join(applicant_resume_dir, f)), reverse=True)
        
        resumes = []
        for filename in files:
            filepath = os.path.join(applicant_resume_dir, filename)
            file_stat = os.stat(filepath)
            resumes.append({
                'filename': filename,
                'path': f"{applicant_id}/{filename}",
                'size': file_stat.st_size,
                'uploaded_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
        
        return {
            'success': True,
            'resumes': resumes,
            'message': 'Resumes retrieved successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'resumes': [],
            'message': f'Error retrieving resumes: {str(e)}'
        }

