import os
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from erp.models import Resume


class Command(BaseCommand):
    help = 'Locate missing resume files in MEDIA_ROOT, move them to proper folders and update Resume records.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show actions without moving files')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            self.stdout.write(self.style.ERROR(f'MEDIA_ROOT does not exist: {media_root}'))
            return

        resumes = Resume.objects.select_related('student', 'student__user').all()
        total_moved = 0
        total_updated = 0
        total_not_found = 0

        # build a list of all files under media for faster lookup
        all_files = []
        for root, dirs, files in os.walk(media_root):
            for f in files:
                all_files.append(Path(root) / f)

        def find_candidates(roll, username, fullname):
            candidates = []
            low_roll = (roll or '').lower()
            low_user = (username or '').lower()
            low_name = (fullname or '').replace(' ', '').lower() if fullname else ''
            for p in all_files:
                name = p.name.lower()
                # match if filename contains roll or username or compact fullname
                if low_roll and low_roll in name:
                    candidates.append(p)
                    continue
                if low_user and low_user in name:
                    candidates.append(p)
                    continue
                if low_name and low_name in name:
                    candidates.append(p)
                    continue
                # also match filenames that include 'resume' and the username/roll
                if 'resume' in name and (low_roll in name or low_user in name or low_name in name):
                    candidates.append(p)
            return list(dict.fromkeys(candidates))  # unique preserving order

        for resume in resumes:
            student = resume.student
            roll = getattr(student, 'roll_number', '')
            username = getattr(student.user, 'username', '') if getattr(student, 'user', None) else ''
            fullname = student.user.get_full_name() if getattr(student, 'user', None) else ''

            # Only handle single resume_file field and place into 'resumes/'
            field = 'resume_file'
            subdir = 'resumes'
            filefield = getattr(resume, field)
            current_name = getattr(filefield, 'name', None) if filefield else None

            # If file exists at recorded path, nothing to do
            if current_name:
                abs_path = media_root / current_name
                if abs_path.exists():
                    continue

            # Try to find candidates
            candidates = find_candidates(roll, username, fullname)

            if not candidates:
                self.stdout.write(self.style.WARNING(f'No candidate found for student {roll} ({username}) field {field}'))
                total_not_found += 1
                continue

            # Choose the most recently modified candidate
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            chosen = candidates[0]

            rel_target_dir = Path(subdir)
            target_dir = media_root / rel_target_dir
            target_dir.mkdir(parents=True, exist_ok=True)

            new_name = rel_target_dir / chosen.name
            target_path = media_root / new_name

            if dry_run:
                self.stdout.write(self.style.NOTICE(f'[dry-run] Would move {chosen} -> {target_path} and update Resume {resume.id}.{field}'))
            else:
                try:
                    # move the file
                    shutil.move(str(chosen), str(target_path))
                    # update filefield name (relative to MEDIA_ROOT)
                    setattr(resume, field, str(new_name).replace('\\', '/'))
                    resume.save()
                    total_moved += 1
                    total_updated += 1
                    self.stdout.write(self.style.SUCCESS(f'Moved {chosen} -> {target_path} and updated Resume {resume.id}.{field}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error moving {chosen} for Resume {resume.id}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Done. Files moved: {total_moved}, records updated: {total_updated}, not found: {total_not_found}'))