#!/usr/bin/env python3
"""
Static Files Debug Script

A small debug script that can be run inside the container to verify whether 
static files exist, their sizes, owner/permissions, and whether Flask's 
static folder exists as expected.

This helps confirm whether the problem is the image or the platform serving responses.

Usage:
    # Basic health check with detailed output
    python debug_static_files.py
    
    # JSON output for automation/monitoring
    python debug_static_files.py --json
    
    # In Docker container
    docker exec <container> python /app/debug_static_files.py

Exit codes:
    0 - All checks passed (healthy)
    1 - Issues detected (unhealthy)

Example output:
    🏥 OVERALL HEALTH: ✅ HEALTHY (when all files are correct)
    🏥 OVERALL HEALTH: ❌ ISSUES DETECTED (when problems found)
"""

import os
import stat
import sys
from pathlib import Path
from typing import Dict, Any
import pwd
import grp


class StaticFilesDebugger:
    """Debug Flask static files configuration and permissions."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent.absolute()
        self.static_dir = self.app_dir / "static"
        self.results = {}
        self.quiet = False
    
    def print_header(self, title: str):
        """Print formatted header."""
        if not self.quiet:
            print(f"\n{'='*60}")
            print(f" {title}")
            print(f"{'='*60}")
    
    def print_section(self, title: str):
        """Print formatted section header."""
        if not self.quiet:
            print(f"\n{'-'*40}")
            print(f" {title}")
            print(f"{'-'*40}")
    
    def get_file_owner_info(self, file_path: Path) -> Dict[str, str]:
        """Get file owner and group information."""
        try:
            stat_info = file_path.stat()
            try:
                owner = pwd.getpwuid(stat_info.st_uid).pw_name
            except KeyError:
                owner = str(stat_info.st_uid)
            
            try:
                group = grp.getgrgid(stat_info.st_gid).gr_name
            except KeyError:
                group = str(stat_info.st_gid)
            
            return {
                'owner': owner,
                'group': group,
                'uid': stat_info.st_uid,
                'gid': stat_info.st_gid
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_file_permissions(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed file permissions."""
        try:
            stat_info = file_path.stat()
            permissions = stat.filemode(stat_info.st_mode)
            
            return {
                'permissions': permissions,
                'mode_octal': oct(stat_info.st_mode)[-3:],
                'readable': os.access(file_path, os.R_OK),
                'writable': os.access(file_path, os.W_OK),
                'executable': os.access(file_path, os.X_OK)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def check_static_directory(self) -> Dict[str, Any]:
        """Check Flask static directory configuration."""
        self.print_section("Flask Static Directory Check")
        
        results = {
            'app_dir': str(self.app_dir),
            'static_dir': str(self.static_dir),
            'static_exists': self.static_dir.exists(),
            'static_is_dir': self.static_dir.is_dir() if self.static_dir.exists() else False
        }
        
        print(f"App Directory: {results['app_dir']}")
        print(f"Static Directory: {results['static_dir']}")
        
        if results['static_exists']:
            if not self.quiet:
                print(f"✅ Static directory exists: {self.static_dir}")
            
            if results['static_is_dir']:
                if not self.quiet:
                    print(f"✅ Static path is a directory")
                
                # Get permissions for static directory
                perms = self.get_file_permissions(self.static_dir)
                owner_info = self.get_file_owner_info(self.static_dir)
                
                if not self.quiet:
                    print(f"   Permissions: {perms.get('permissions', 'unknown')}")
                    print(f"   Owner: {owner_info.get('owner', 'unknown')}:{owner_info.get('group', 'unknown')}")
                    print(f"   Readable: {perms.get('readable', False)}")
                    print(f"   Executable: {perms.get('executable', False)}")
                
                results.update({
                    'permissions': perms,
                    'owner_info': owner_info
                })
            else:
                if not self.quiet:
                    print(f"❌ Static path exists but is not a directory")
        else:
            if not self.quiet:
                print(f"❌ Static directory does not exist: {self.static_dir}")
        
        self.results['static_directory'] = results
        return results
    
    def check_static_files(self) -> Dict[str, Any]:
        """Check individual static files."""
        self.print_section("Static Files Check")
        
        # Expected static files
        static_files = {
            'css/dashboard.css': 'Dashboard CSS file',
            'js/dashboard.js': 'Dashboard JavaScript file'
        }
        
        results = {}
        
        for relative_path, description in static_files.items():
            file_path = self.static_dir / relative_path
            file_results = {
                'path': str(file_path),
                'description': description,
                'exists': file_path.exists()
            }
            
            print(f"\n📁 {description}")
            print(f"   Path: {file_path}")
            
            if file_results['exists']:
                print(f"   ✅ File exists")
                
                # Get file size
                try:
                    size = file_path.stat().st_size
                    file_results['size'] = size
                    print(f"   📊 Size: {size:,} bytes ({size/1024:.1f} KB)")
                except Exception as e:
                    print(f"   ❌ Error getting size: {e}")
                    file_results['size_error'] = str(e)
                
                # Get permissions
                perms = self.get_file_permissions(file_path)
                file_results['permissions'] = perms
                
                if 'error' in perms:
                    print(f"   ❌ Permission error: {perms['error']}")
                else:
                    print(f"   🔒 Permissions: {perms['permissions']}")
                    print(f"   📖 Readable: {perms['readable']}")
                
                # Get owner info
                owner_info = self.get_file_owner_info(file_path)
                file_results['owner_info'] = owner_info
                
                if 'error' in owner_info:
                    print(f"   ❌ Owner info error: {owner_info['error']}")
                else:
                    print(f"   👤 Owner: {owner_info['owner']}:{owner_info['group']}")
                
                # Try to read a small portion of the file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_preview = f.read(100)
                    file_results['readable_content'] = True
                    print(f"   ✅ File is readable")
                    print(f"   📝 Content preview: {content_preview[:50]}{'...' if len(content_preview) > 50 else ''}")
                except Exception as e:
                    file_results['readable_content'] = False
                    file_results['read_error'] = str(e)
                    print(f"   ❌ Cannot read file: {e}")
            else:
                print(f"   ❌ File does not exist")
            
            results[relative_path] = file_results
        
        self.results['static_files'] = results
        return results
    
    def check_flask_configuration(self) -> Dict[str, Any]:
        """Check Flask static folder configuration."""
        self.print_section("Flask Configuration Check")
        
        results = {}
        
        try:
            # Try to import Flask app to check configuration
            sys.path.insert(0, str(self.app_dir))
            
            # Check if we can import the web server
            try:
                import web_server
                app = web_server.app
                
                results['flask_import'] = True
                results['static_folder'] = app.static_folder
                results['static_url_path'] = app.static_url_path
                
                print(f"✅ Flask app imported successfully")
                print(f"📁 Static folder: {app.static_folder}")
                print(f"🌐 Static URL path: {app.static_url_path}")
                
                # Check if the configured static folder matches our expectation
                expected_static = str(self.static_dir)
                actual_static = os.path.abspath(app.static_folder) if app.static_folder else None
                
                if actual_static:
                    results['static_folder_absolute'] = actual_static
                    print(f"📍 Absolute static path: {actual_static}")
                    
                    if actual_static == expected_static:
                        print(f"✅ Static folder configuration matches expected path")
                        results['static_path_correct'] = True
                    else:
                        print(f"⚠️  Static folder mismatch!")
                        print(f"    Expected: {expected_static}")
                        print(f"    Actual:   {actual_static}")
                        results['static_path_correct'] = False
                else:
                    print(f"❌ Flask static folder is None")
                    results['static_path_correct'] = False
                
            except Exception as e:
                results['flask_import'] = False
                results['import_error'] = str(e)
                print(f"❌ Error importing Flask app: {e}")
        
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ Error checking Flask configuration: {e}")
        
        self.results['flask_configuration'] = results
        return results
    
    def check_current_user(self) -> Dict[str, Any]:
        """Check current user and permissions context."""
        self.print_section("Current User Context")
        
        results = {}
        
        try:
            import getpass
            current_user = getpass.getuser()
            results['username'] = current_user
            print(f"👤 Current user: {current_user}")
            
            # Get user ID and group ID
            results['uid'] = os.getuid()
            results['gid'] = os.getgid()
            print(f"🆔 UID: {results['uid']}, GID: {results['gid']}")
            
            # Get working directory
            results['cwd'] = os.getcwd()
            print(f"📁 Working directory: {results['cwd']}")
            
            # Check if we're in a container (common indicators)
            container_indicators = [
                ('/.dockerenv', 'Docker container'),
                ('/proc/1/cgroup', 'Container cgroup')
            ]
            
            results['container_indicators'] = {}
            for path, description in container_indicators:
                exists = os.path.exists(path)
                results['container_indicators'][path] = exists
                if exists:
                    print(f"🐳 {description} detected: {path}")
        
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ Error checking user context: {e}")
        
        self.results['user_context'] = results
        return results
    
    def generate_summary(self):
        """Generate a summary of findings."""
        self.print_header("SUMMARY & RECOMMENDATIONS")
        
        issues = []
        recommendations = []
        
        # Check static directory issues
        static_dir_results = self.results.get('static_directory', {})
        if not static_dir_results.get('static_exists'):
            issues.append("Static directory does not exist")
            recommendations.append("Create static directory with proper permissions")
        elif not static_dir_results.get('static_is_dir'):
            issues.append("Static path exists but is not a directory")
            recommendations.append("Remove conflicting file and create static directory")
        
        # Check static files issues
        static_files_results = self.results.get('static_files', {})
        missing_files = []
        unreadable_files = []
        
        for file_path, file_info in static_files_results.items():
            if not file_info.get('exists'):
                missing_files.append(file_path)
            elif not file_info.get('readable_content', True):
                unreadable_files.append(file_path)
        
        if missing_files:
            issues.append(f"Missing static files: {', '.join(missing_files)}")
            recommendations.append("Ensure all required static files are present in the image")
        
        if unreadable_files:
            issues.append(f"Unreadable static files: {', '.join(unreadable_files)}")
            recommendations.append("Check file permissions for static files")
        
        # Check Flask configuration issues
        flask_results = self.results.get('flask_configuration', {})
        if not flask_results.get('flask_import'):
            issues.append("Cannot import Flask application")
            recommendations.append("Check Flask application and dependencies")
        elif not flask_results.get('static_path_correct'):
            issues.append("Flask static folder configuration mismatch")
            recommendations.append("Verify Flask static folder configuration")
        
        # Display results
        print("\n🔍 ISSUES IDENTIFIED:")
        if issues:
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("  ✅ No major issues detected!")
        
        print("\n💡 RECOMMENDATIONS:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("  ✅ Static files configuration appears correct!")
        
        # Overall health
        healthy = len(issues) == 0
        print(f"\n🏥 OVERALL HEALTH: {'✅ HEALTHY' if healthy else '❌ ISSUES DETECTED'}")
        
        return {
            'healthy': healthy,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def run_debug(self, quiet=False):
        """Run complete static files debug suite."""
        self.quiet = quiet
        
        if not quiet:
            self.print_header("STATIC FILES DEBUG REPORT")
            print("Checking Flask static files configuration and permissions...")
            print(f"Script location: {__file__}")
            print(f"App directory: {self.app_dir}")
        
        # Run all checks
        self.check_current_user()
        self.check_static_directory()
        self.check_static_files()
        self.check_flask_configuration()
        
        # Generate summary
        if not quiet:
            summary = self.generate_summary()
        else:
            # Generate summary silently for JSON output
            issues = []
            recommendations = []
            
            # Check issues without printing
            static_dir_results = self.results.get('static_directory', {})
            if not static_dir_results.get('static_exists'):
                issues.append("Static directory does not exist")
                recommendations.append("Create static directory with proper permissions")
            elif not static_dir_results.get('static_is_dir'):
                issues.append("Static path exists but is not a directory")
                recommendations.append("Remove conflicting file and create static directory")
            
            static_files_results = self.results.get('static_files', {})
            missing_files = []
            unreadable_files = []
            
            for file_path, file_info in static_files_results.items():
                if not file_info.get('exists'):
                    missing_files.append(file_path)
                elif not file_info.get('readable_content', True):
                    unreadable_files.append(file_path)
            
            if missing_files:
                issues.append(f"Missing static files: {', '.join(missing_files)}")
                recommendations.append("Ensure all required static files are present in the image")
            
            if unreadable_files:
                issues.append(f"Unreadable static files: {', '.join(unreadable_files)}")
                recommendations.append("Check file permissions for static files")
            
            flask_results = self.results.get('flask_configuration', {})
            if not flask_results.get('flask_import'):
                issues.append("Cannot import Flask application")
                recommendations.append("Check Flask application and dependencies")
            elif not flask_results.get('static_path_correct'):
                issues.append("Flask static folder configuration mismatch")
                recommendations.append("Verify Flask static folder configuration")
            
            summary = {
                'healthy': len(issues) == 0,
                'issues': issues,
                'recommendations': recommendations
            }
        
        return {
            'summary': summary,
            'detailed_results': self.results
        }


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug Flask static files configuration')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    debugger = StaticFilesDebugger()
    results = debugger.run_debug(quiet=args.json)
    
    if args.json:
        import json
        print(json.dumps(results, indent=2, default=str))
    
    # Exit with appropriate code
    sys.exit(0 if results['summary']['healthy'] else 1)


if __name__ == "__main__":
    main()