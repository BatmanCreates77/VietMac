#!/usr/bin/env python3
"""
Spec Parser - Extract structured data from MacBook product names
"""

import re
from typing import Dict, Optional


class SpecParser:
    """Parse MacBook specifications from product names"""

    def __init__(self):
        # Regex patterns for extracting specs
        self.patterns = {
            'chip': r'(M1|M2|M3|M4|M5)(?:\s*(Pro|Max))?',
            'screen': r'(\d+(?:\.\d+)?)\s*(?:inch|"|\'\')',
            'cpu': r'(\d+)\s*(?:CPU|core\s*CPU|C)',
            'gpu': r'(\d+)\s*(?:GPU|core\s*GPU|G)',
            'ram': r'(\d+)\s*GB(?!\s*SSD)',
            'storage': r'(\d+)\s*(?:GB|TB)(?:\s*SSD)?',
            'year': r'(20\d{2})',
        }

    def parse(self, product_name: str) -> Dict:
        """
        Parse a MacBook product name and extract structured specs

        Args:
            product_name: Raw product name from shop

        Returns:
            Dictionary with parsed specs
        """
        if not product_name:
            return {}

        # Normalize name
        name = product_name.strip()

        # Extract model type
        model_type = self._extract_model_type(name)

        # Extract chip
        chip_info = self._extract_chip(name)

        # Extract screen size
        screen_size = self._extract_screen_size(name)

        # Extract CPU cores
        cpu_cores = self._extract_cpu_cores(name)

        # Extract GPU cores
        gpu_cores = self._extract_gpu_cores(name)

        # Extract RAM
        ram_gb = self._extract_ram(name)

        # Extract storage
        storage_info = self._extract_storage(name)

        # Extract year
        year = self._extract_year(name)

        # Generate clean model name
        clean_name = self._generate_clean_name(
            model_type, chip_info, screen_size, cpu_cores, gpu_cores, ram_gb, storage_info
        )

        # Generate unique ID
        product_id = self._generate_id(chip_info, model_type, screen_size, ram_gb, storage_info)

        return {
            'id': product_id,
            'model_type': model_type,
            'chip': chip_info['chip'],
            'chip_variant': chip_info['variant'],
            'screen_size': screen_size,
            'cpu_cores': cpu_cores,
            'gpu_cores': gpu_cores,
            'ram_gb': ram_gb,
            'storage_gb': storage_info['gb'],
            'storage_display': storage_info['display'],
            'year': year,
            'clean_name': clean_name,
            'raw_name': product_name,
        }

    def _extract_model_type(self, name: str) -> str:
        """Extract MacBook Air or MacBook Pro"""
        name_lower = name.lower()
        if 'air' in name_lower:
            return 'MacBook Air'
        elif 'pro' in name_lower:
            return 'MacBook Pro'
        return 'MacBook'

    def _extract_chip(self, name: str) -> Dict:
        """Extract chip (M1, M2, M3, M4, M5) and variant (Pro, Max)"""
        match = re.search(self.patterns['chip'], name, re.IGNORECASE)
        if match:
            chip = match.group(1).upper()
            variant = match.group(2).title() if match.group(2) else None
            full_chip = f"{chip} {variant}" if variant else chip
            return {'chip': chip, 'variant': variant, 'full': full_chip}
        return {'chip': None, 'variant': None, 'full': None}

    def _extract_screen_size(self, name: str) -> Optional[str]:
        """Extract screen size (13, 14, 15, 16 inch)"""
        match = re.search(self.patterns['screen'], name)
        if match:
            size = match.group(1)
            # Normalize to integer if possible
            if '.' not in size:
                return f"{size}\""
            return f"{size}\""
        return None

    def _extract_cpu_cores(self, name: str) -> Optional[int]:
        """Extract CPU core count"""
        # Look for patterns like "10CPU", "10 CPU", "10 core CPU", "10C"
        patterns = [
            r'(\d+)\s*CPU',
            r'(\d+)\s*core\s*CPU',
            r'(\d+)\s*C(?:PU)?(?:\s|,|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_gpu_cores(self, name: str) -> Optional[int]:
        """Extract GPU core count"""
        # Look for patterns like "10GPU", "10 GPU", "10 core GPU", "10G"
        patterns = [
            r'(\d+)\s*GPU',
            r'(\d+)\s*core\s*GPU',
            r'(\d+)\s*G(?:PU)?(?:\s|,|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_ram(self, name: str) -> Optional[int]:
        """Extract RAM in GB"""
        # Find GB that's NOT followed by SSD (to avoid storage)
        match = re.search(r'(\d+)\s*GB(?!\s*SSD)', name, re.IGNORECASE)
        if match:
            # Sometimes there are multiple GB mentions, try to find RAM specifically
            ram_patterns = [
                r'(\d+)\s*GB\s*RAM',
                r'RAM\s*(\d+)\s*GB',
                r'(\d+)\s*GB(?!\s*SSD)',  # Fallback
            ]

            for pattern in ram_patterns:
                ram_match = re.search(pattern, name, re.IGNORECASE)
                if ram_match:
                    return int(ram_match.group(1))
        return None

    def _extract_storage(self, name: str) -> Dict:
        """Extract storage (GB or TB)"""
        # Look for storage patterns with SSD keyword first
        patterns = [
            r'(\d+)\s*TB(?:\s*SSD)?',
            r'(\d+)\s*GB\s*SSD',
            r'SSD\s*(\d+)\s*(?:GB|TB)',
        ]

        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                is_tb = 'TB' in match.group(0).upper()

                if is_tb:
                    return {
                        'gb': value * 1024,
                        'display': f"{value}TB"
                    }
                else:
                    return {
                        'gb': value,
                        'display': f"{value}GB"
                    }

        # Fallback: Find all GB/TB mentions and assume last one (after RAM) is storage
        # This handles formats like "16GB 512GB" where first is RAM, second is storage
        all_storage_matches = list(re.finditer(r'(\d+)\s*(GB|TB)(?!\s*RAM)', name, re.IGNORECASE))
        if len(all_storage_matches) >= 2:
            # If we have 2+ matches, the last one is likely storage
            last_match = all_storage_matches[-1]
            value = int(last_match.group(1))
            unit = last_match.group(2).upper()
            if unit == 'TB':
                return {
                    'gb': value * 1024,
                    'display': f"{value}TB"
                }
            else:
                return {
                    'gb': value,
                    'display': f"{value}GB"
                }

        return {'gb': None, 'display': None}

    def _extract_year(self, name: str) -> Optional[int]:
        """Extract year (2020, 2021, etc.)"""
        match = re.search(self.patterns['year'], name)
        if match:
            return int(match.group(1))
        return None

    def _generate_clean_name(self, model_type, chip_info, screen_size,
                            cpu_cores, gpu_cores, ram_gb, storage_info):
        """Generate a clean, standardized product name"""
        parts = []

        # Model type and screen
        if model_type:
            parts.append(model_type)
        if screen_size:
            parts.append(screen_size)

        # Chip
        if chip_info['full']:
            parts.append(chip_info['full'])

        # CPU/GPU
        if cpu_cores:
            parts.append(f"{cpu_cores}C")
        if gpu_cores:
            parts.append(f"{gpu_cores}G")

        # RAM
        if ram_gb:
            parts.append(f"{ram_gb}GB")

        # Storage
        if storage_info['display']:
            parts.append(storage_info['display'])

        return ' '.join(parts) if parts else None

    def _generate_id(self, chip_info, model_type, screen_size, ram_gb, storage_info):
        """Generate unique product ID"""
        parts = []

        # Chip
        if chip_info['chip']:
            chip_id = chip_info['chip'].lower()
            if chip_info['variant']:
                chip_id += '-' + chip_info['variant'].lower()
            parts.append(chip_id)

        # Model type
        if model_type:
            if 'Air' in model_type:
                parts.append('air')
            elif 'Pro' in model_type:
                parts.append('pro')

        # Screen
        if screen_size:
            parts.append(screen_size.replace('"', ''))

        # RAM
        if ram_gb:
            parts.append(str(ram_gb))

        # Storage
        if storage_info['gb']:
            if storage_info['gb'] >= 1024:
                parts.append(f"{storage_info['gb']//1024}tb")
            else:
                parts.append(f"{storage_info['gb']}gb")

        return '-'.join(parts) if parts else None


def test_parser():
    """Test the spec parser"""
    parser = SpecParser()

    test_cases = [
        "MacBook Pro 14 M4 10CPU 10GPU 16GB 512GB",
        "MacBook Air 13.6 inch M3 | 8 core CPU | 8 core GPU | 8GB RAM | SSD 256GB",
        "MacBook Air M4 13 inch 2025 10CPU 10GPU 16GB 512GB",
        "MacBook Pro 16 M4 Max 16CPU 40GPU 48GB 1TB",
        "Apple MacBook Air M1 256GB 2020",
        "MacBook Pro 14 inch M3 Pro 11 core CPU 14 core GPU 18GB RAM 512GB SSD",
    ]

    print("Testing Spec Parser:")
    print("="*80)

    for test in test_cases:
        result = parser.parse(test)
        print(f"\nInput: {test}")
        print(f"ID: {result['id']}")
        print(f"Clean Name: {result['clean_name']}")
        print(f"Chip: {result['chip']} {result['chip_variant'] or ''}")
        print(f"Screen: {result['screen_size']}")
        print(f"CPU/GPU: {result['cpu_cores']}C / {result['gpu_cores']}G")
        print(f"RAM: {result['ram_gb']}GB")
        print(f"Storage: {result['storage_display']}")


if __name__ == '__main__':
    test_parser()
