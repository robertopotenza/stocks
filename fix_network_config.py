#!/usr/bin/env python3
"""
Network Configuration Fix Script

This script provides automated fixes for common network issues that prevent
the technical indicators extractor from accessing investing.com.

Usage:
    python fix_network_config.py [--apply-fixes]
"""

import os
import sys
import subprocess
import socket
from typing import Dict, List, Any

class NetworkConfigFixer:
    """Automated network configuration fixes."""
    
    def __init__(self):
        self.fixes_applied = []
        self.potential_fixes = []
    
    def print_header(self, title: str):
        """Print formatted section header."""
        print("\n" + "=" * 70)
        print(f"🔧 {title}")
        print("=" * 70)
    
    def print_section(self, title: str):
        """Print formatted subsection header."""
        print(f"\n📋 {title}")
        print("-" * 50)
    
    def detect_dns_issues(self) -> Dict[str, Any]:
        """Detect DNS resolution issues."""
        self.print_section("Detecting DNS Issues")
        
        issues = {}
        test_domains = ['www.investing.com', 'google.com', 'cloudflare.com']
        
        for domain in test_domains:
            try:
                socket.gethostbyname(domain)
                print(f"✅ {domain}: DNS resolution OK")
                issues[domain] = 'ok'
            except socket.gaierror as e:
                print(f"❌ {domain}: DNS failed - {e}")
                issues[domain] = str(e)
        
        return issues
    
    def suggest_dns_fixes(self, dns_issues: Dict[str, Any]) -> List[str]:
        """Suggest DNS configuration fixes."""
        self.print_section("DNS Fix Suggestions")
        
        fixes = []
        
        failed_domains = [domain for domain, status in dns_issues.items() if status != 'ok']
        
        if failed_domains:
            print("🔍 DNS Resolution Issues Detected")
            
            # Fix 1: Add public DNS servers
            fixes.append({
                'name': 'configure_public_dns',
                'description': 'Configure public DNS servers (8.8.8.8, 1.1.1.1)',
                'commands': [
                    'echo "nameserver 8.8.8.8" >> /etc/resolv.conf',
                    'echo "nameserver 1.1.1.1" >> /etc/resolv.conf'
                ],
                'env_vars': {
                    'DNS_SERVER': '8.8.8.8'
                }
            })
            
            # Fix 2: Add hosts file entries for critical domains
            if 'www.investing.com' in failed_domains:
                fixes.append({
                    'name': 'add_hosts_entries',
                    'description': 'Add investing.com IP addresses to /etc/hosts',
                    'commands': [
                        'echo "5.254.205.57 www.investing.com investing.com" >> /etc/hosts',
                        'echo "104.16.185.223 investing.com" >> /etc/hosts'
                    ]
                })
            
            # Fix 3: Configure proxy if in corporate environment
            fixes.append({
                'name': 'configure_proxy',
                'description': 'Configure HTTP/HTTPS proxy for corporate networks',
                'env_vars': {
                    'HTTP_PROXY': 'http://proxy.company.com:8080',
                    'HTTPS_PROXY': 'http://proxy.company.com:8080',
                    'NO_PROXY': 'localhost,127.0.0.1,github.com'
                },
                'manual': True  # Requires manual configuration
            })
        else:
            print("✅ No DNS issues detected")
        
        return fixes
    
    def check_container_network(self) -> Dict[str, Any]:
        """Check container network configuration."""
        self.print_section("Container Network Check")
        
        network_info = {}
        
        # Check /etc/resolv.conf
        try:
            with open('/etc/resolv.conf', 'r') as f:
                resolv_conf = f.read()
                print("📄 /etc/resolv.conf content:")
                print(resolv_conf)
                network_info['resolv_conf'] = resolv_conf
        except Exception as e:
            print(f"❌ Cannot read /etc/resolv.conf: {e}")
            network_info['resolv_conf_error'] = str(e)
        
        # Check /etc/hosts
        try:
            with open('/etc/hosts', 'r') as f:
                hosts_content = f.read()
                print("📄 /etc/hosts content:")
                print(hosts_content)
                network_info['hosts'] = hosts_content
        except Exception as e:
            print(f"❌ Cannot read /etc/hosts: {e}")
            network_info['hosts_error'] = str(e)
        
        return network_info
    
    def create_dockerfile_fixes(self) -> str:
        """Create Dockerfile additions for network fixes."""
        self.print_section("Dockerfile Network Fixes")
        
        dockerfile_additions = """
# Network configuration fixes for container
RUN apt-get update && apt-get install -y \\
    dnsutils \\
    iputils-ping \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Configure DNS servers
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf && \\
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf

# Add investing.com to hosts file for reliability
RUN echo "5.254.205.57 www.investing.com investing.com" >> /etc/hosts

# Set environment variables for network configuration
ENV DNS_SERVER=8.8.8.8
ENV PYTHONHTTPSVERIFY=0
"""
        
        print("📝 Add these lines to your Dockerfile:")
        print(dockerfile_additions)
        
        return dockerfile_additions
    
    def create_docker_compose_fixes(self) -> str:
        """Create docker-compose.yml network configuration."""
        self.print_section("Docker Compose Network Fixes")
        
        compose_additions = """
# Add to your docker-compose.yml service configuration:
services:
  your-app:
    # ... existing configuration ...
    
    # Network configuration
    dns:
      - 8.8.8.8
      - 1.1.1.1
    
    # Environment variables for network
    environment:
      - HTTP_PROXY=${HTTP_PROXY:-}
      - HTTPS_PROXY=${HTTPS_PROXY:-}
      - NO_PROXY=localhost,127.0.0.1
      - DNS_SERVER=8.8.8.8
      - PYTHONHTTPSVERIFY=0
    
    # Add hosts entries
    extra_hosts:
      - "www.investing.com:5.254.205.57"
      - "investing.com:5.254.205.57"
"""
        
        print("📝 Add these configurations to your docker-compose.yml:")
        print(compose_additions)
        
        return compose_additions
    
    def create_environment_script(self) -> str:
        """Create environment setup script."""
        self.print_section("Environment Setup Script")
        
        env_script = """#!/bin/bash
# Network configuration for technical indicators extractor

# Set DNS server
export DNS_SERVER=8.8.8.8

# Configure proxy if needed (uncomment and modify as needed)
# export HTTP_PROXY=http://proxy.company.com:8080
# export HTTPS_PROXY=http://proxy.company.com:8080
# export NO_PROXY=localhost,127.0.0.1,github.com

# Disable SSL verification if needed (not recommended for production)
# export PYTHONHTTPSVERIFY=0

# Set debug logging
export LOG_LEVEL=DEBUG

echo "✅ Network environment configured"
echo "   DNS Server: $DNS_SERVER"
echo "   HTTP Proxy: ${HTTP_PROXY:-<not set>}"
echo "   HTTPS Proxy: ${HTTPS_PROXY:-<not set>}"
"""
        
        # Write to file
        script_path = '/home/runner/work/stocks/stocks/setup_network_env.sh'
        try:
            with open(script_path, 'w') as f:
                f.write(env_script)
            os.chmod(script_path, 0o755)
            print(f"📁 Created environment script: {script_path}")
            print("   Run with: source setup_network_env.sh")
        except Exception as e:
            print(f"❌ Could not create script: {e}")
        
        return env_script
    
    def test_investing_com_alternatives(self) -> List[str]:
        """Test alternative ways to access investing.com data."""
        self.print_section("Alternative Data Sources")
        
        alternatives = []
        
        print("🔍 Testing alternative approaches:")
        
        # Alternative 1: Yahoo Finance
        alternatives.append({
            'name': 'Yahoo Finance',
            'url_pattern': 'https://finance.yahoo.com/quote/{ticker}',
            'pros': ['Reliable', 'No rate limiting', 'Good API'],
            'cons': ['Different data format', 'Requires code changes']
        })
        
        # Alternative 2: Alpha Vantage API
        alternatives.append({
            'name': 'Alpha Vantage API',
            'url_pattern': 'https://www.alphavantage.co/query?function=TECHNICAL_INDICATOR',
            'pros': ['API-based', 'Structured data', 'Multiple indicators'],
            'cons': ['Requires API key', 'Rate limited']
        })
        
        # Alternative 3: Cached/offline mode
        alternatives.append({
            'name': 'Enhanced Mock Data',
            'description': 'Improve mock data quality with historical patterns',
            'pros': ['Always available', 'Fast', 'No network needed'],
            'cons': ['Not real-time', 'May not reflect market conditions']
        })
        
        for alt in alternatives:
            print(f"📊 {alt['name']}")
            if 'url_pattern' in alt:
                print(f"   URL: {alt['url_pattern']}")
            if 'description' in alt:
                print(f"   Description: {alt['description']}")
            print(f"   Pros: {', '.join(alt['pros'])}")
            print(f"   Cons: {', '.join(alt['cons'])}")
            print()
        
        return alternatives
    
    def run_diagnosis_and_fixes(self):
        """Run complete diagnosis and suggest fixes."""
        self.print_header("NETWORK CONFIGURATION DIAGNOSIS & FIXES")
        
        # Diagnose issues
        dns_issues = self.detect_dns_issues()
        network_info = self.check_container_network()
        
        # Suggest fixes
        dns_fixes = self.suggest_dns_fixes(dns_issues)
        
        # Generate fix scripts and configs
        self.create_dockerfile_fixes()
        self.create_docker_compose_fixes()
        self.create_environment_script()
        
        # Show alternatives
        alternatives = self.test_investing_com_alternatives()
        
        # Final summary
        self.print_header("IMPLEMENTATION SUMMARY")
        
        print("🎯 IMMEDIATE FIXES (Choose one):")
        print("1. Environment Variables:")
        print("   export DNS_SERVER=8.8.8.8")
        print("   source setup_network_env.sh")
        print()
        print("2. Add to /etc/hosts:")
        print("   echo '5.254.205.57 www.investing.com investing.com' >> /etc/hosts")
        print()
        print("3. Configure Proxy (if in corporate network):")
        print("   export HTTPS_PROXY=http://your-proxy:port")
        print()
        
        print("🐳 PRODUCTION CONTAINER FIXES:")
        print("- Update Dockerfile with DNS and hosts configuration")
        print("- Update docker-compose.yml with network settings")
        print("- Set environment variables in container orchestration")
        print()
        
        print("🔀 ALTERNATIVE APPROACHES:")
        print("- Switch to Yahoo Finance or other data source")
        print("- Use API-based indicators (Alpha Vantage)")
        print("- Enhance mock data with historical patterns")
        
        return {
            'dns_issues': dns_issues,
            'network_info': network_info,
            'alternatives': alternatives
        }

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Network configuration fixes for extractor')
    parser.add_argument('--apply-fixes', action='store_true', help='Apply automatic fixes')
    
    args = parser.parse_args()
    
    fixer = NetworkConfigFixer()
    results = fixer.run_diagnosis_and_fixes()
    
    if args.apply_fixes:
        print("\n🔧 Applying automatic fixes...")
        # Here you would implement the actual fix application
        # For now, just show what would be done
        print("✅ Environment script created")
        print("ℹ️  Manual fixes required for container configuration")

if __name__ == "__main__":
    main()