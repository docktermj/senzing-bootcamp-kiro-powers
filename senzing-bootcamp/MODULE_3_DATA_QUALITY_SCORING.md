# Module 3: Evaluate Data Quality with Automated Scoring

## Overview

Module 3 evaluates data quality using automated scoring and metrics. This module provides objective measurements to help you understand data readiness for entity resolution.

## Purpose

After collecting data sources in Module 2, you need to assess their quality before mapping. Module 3 provides:

1. **Automated Quality Scoring** (0-100 scale)
2. **Attribute Completeness Metrics**
3. **Data Consistency Analysis**
4. **Visual Quality Dashboard**
5. **Actionable Recommendations**

## Quality Scoring System

### Overall Quality Score (0-100)

The quality score is calculated from multiple factors:

```
Quality Score = (
    Completeness Score × 0.40 +
    Consistency Score × 0.30 +
    Validity Score × 0.20 +
    Uniqueness Score × 0.10
)
```

### Score Interpretation

- **90-100**: Excellent - Ready for entity resolution
- **75-89**: Good - Minor improvements recommended
- **60-74**: Fair - Moderate data quality issues
- **40-59**: Poor - Significant quality problems
- **0-39**: Critical - Major data quality work needed

## Quality Metrics

### 1. Completeness Score (40% weight)

Measures how complete the data is:

```python
# Calculate completeness for each field
field_completeness = {
    field: (non_null_count / total_records) * 100
    for field in fields
}

# Weight by importance
critical_fields = ['name', 'id', 'address', 'phone', 'email']
completeness_score = (
    sum(field_completeness[f] for f in critical_fields if f in fields) /
    len([f for f in critical_fields if f in fields])
)
```

**Metrics**:
- Percentage of non-null values per field
- Critical field coverage
- Optional field coverage
- Empty string detection

### 2. Consistency Score (30% weight)

Measures data format consistency:

```python
# Check format consistency
format_consistency = {
    'phone': check_phone_format_consistency(data['phone']),
    'email': check_email_format_consistency(data['email']),
    'date': check_date_format_consistency(data['date']),
    'address': check_address_format_consistency(data['address'])
}

consistency_score = average(format_consistency.values())
```

**Metrics**:
- Phone number format consistency
- Email format consistency
- Date format consistency
- Address format consistency
- Name format consistency (UPPER, lower, Title Case)

### 3. Validity Score (20% weight)

Measures data validity:

```python
# Check data validity
validity_checks = {
    'email': validate_email_format(data['email']),
    'phone': validate_phone_format(data['phone']),
    'date': validate_date_range(data['date']),
    'zip': validate_zip_code(data['zip']),
    'state': validate_state_code(data['state'])
}

validity_score = (
    sum(validity_checks.values()) / len(validity_checks)
) * 100
```

**Metrics**:
- Email format validity
- Phone number validity
- Date range validity
- Postal code validity
- State/country code validity

### 4. Uniqueness Score (10% weight)

Measures duplicate detection within source:

```python
# Calculate uniqueness
total_records = len(data)
unique_records = len(data.drop_duplicates(subset=['id']))
exact_duplicates = total_records - unique_records

# Check for fuzzy duplicates
fuzzy_duplicates = detect_fuzzy_duplicates(data)

uniqueness_score = (
    (total_records - exact_duplicates - fuzzy_duplicates) /
    total_records
) * 100
```

**Metrics**:
- Exact duplicate percentage
- Fuzzy duplicate percentage
- ID uniqueness
- Record-level uniqueness

## Automated Quality Assessment

### Python Script Example

```python
#!/usr/bin/env python3
"""
Data Quality Scorer
Analyzes data quality and generates comprehensive report
"""

import pandas as pd
import json
from typing import Dict, List, Tuple
from collections import Counter
import re

class DataQualityScorer:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.data = self.load_data()
        self.report = {}
    
    def load_data(self) -> pd.DataFrame:
        """Load data from CSV or JSON"""
        if self.data_path.endswith('.csv'):
            return pd.read_csv(self.data_path)
        elif self.data_path.endswith('.json') or self.data_path.endswith('.jsonl'):
            return pd.read_json(self.data_path, lines=True)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path}")
    
    def calculate_completeness(self) -> Dict:
        """Calculate completeness metrics"""
        total_records = len(self.data)
        
        field_completeness = {}
        for column in self.data.columns:
            non_null = self.data[column].notna().sum()
            non_empty = (self.data[column].astype(str).str.strip() != '').sum()
            
            field_completeness[column] = {
                'non_null_pct': (non_null / total_records) * 100,
                'non_empty_pct': (non_empty / total_records) * 100,
                'null_count': total_records - non_null,
                'empty_count': total_records - non_empty
            }
        
        # Calculate overall completeness
        critical_fields = self.identify_critical_fields()
        if critical_fields:
            completeness_score = sum(
                field_completeness[f]['non_empty_pct']
                for f in critical_fields
            ) / len(critical_fields)
        else:
            completeness_score = sum(
                fc['non_empty_pct']
                for fc in field_completeness.values()
            ) / len(field_completeness)
        
        return {
            'score': completeness_score,
            'field_details': field_completeness,
            'critical_fields': critical_fields
        }
    
    def identify_critical_fields(self) -> List[str]:
        """Identify critical fields for entity resolution"""
        critical_patterns = [
            r'.*name.*', r'.*id.*', r'.*address.*',
            r'.*phone.*', r'.*email.*', r'.*ssn.*',
            r'.*dob.*', r'.*birth.*'
        ]
        
        critical_fields = []
        for column in self.data.columns:
            for pattern in critical_patterns:
                if re.match(pattern, column.lower()):
                    critical_fields.append(column)
                    break
        
        return critical_fields
    
    def calculate_consistency(self) -> Dict:
        """Calculate format consistency"""
        consistency_checks = {}
        
        # Phone number consistency
        phone_cols = [c for c in self.data.columns if 'phone' in c.lower()]
        for col in phone_cols:
            consistency_checks[col] = self.check_phone_consistency(self.data[col])
        
        # Email consistency
        email_cols = [c for c in self.data.columns if 'email' in c.lower()]
        for col in email_cols:
            consistency_checks[col] = self.check_email_consistency(self.data[col])
        
        # Date consistency
        date_cols = [c for c in self.data.columns if any(d in c.lower() for d in ['date', 'dob', 'birth'])]
        for col in date_cols:
            consistency_checks[col] = self.check_date_consistency(self.data[col])
        
        # Calculate overall consistency score
        if consistency_checks:
            consistency_score = sum(
                c['consistency_pct'] for c in consistency_checks.values()
            ) / len(consistency_checks)
        else:
            consistency_score = 100  # No consistency issues if no fields to check
        
        return {
            'score': consistency_score,
            'field_details': consistency_checks
        }
    
    def check_phone_consistency(self, series: pd.Series) -> Dict:
        """Check phone number format consistency"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return {'consistency_pct': 100, 'formats': {}}
        
        # Detect formats
        formats = Counter()
        for phone in non_null.astype(str):
            if re.match(r'^\d{10}$', phone):
                formats['10_digits'] += 1
            elif re.match(r'^\d{3}-\d{3}-\d{4}$', phone):
                formats['dashed'] += 1
            elif re.match(r'^\(\d{3}\) \d{3}-\d{4}$', phone):
                formats['parentheses'] += 1
            elif re.match(r'^\+\d{11}$', phone):
                formats['international'] += 1
            else:
                formats['other'] += 1
        
        # Most common format
        if formats:
            most_common_count = formats.most_common(1)[0][1]
            consistency_pct = (most_common_count / len(non_null)) * 100
        else:
            consistency_pct = 0
        
        return {
            'consistency_pct': consistency_pct,
            'formats': dict(formats),
            'recommendation': 'Standardize to single format'
        }
    
    def check_email_consistency(self, series: pd.Series) -> Dict:
        """Check email format consistency"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return {'consistency_pct': 100, 'issues': []}
        
        valid_count = 0
        issues = []
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in non_null.astype(str):
            if re.match(email_pattern, email):
                valid_count += 1
            else:
                issues.append(email)
        
        consistency_pct = (valid_count / len(non_null)) * 100
        
        return {
            'consistency_pct': consistency_pct,
            'valid_count': valid_count,
            'invalid_count': len(issues),
            'sample_issues': issues[:5]
        }
    
    def check_date_consistency(self, series: pd.Series) -> Dict:
        """Check date format consistency"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return {'consistency_pct': 100, 'formats': {}}
        
        formats = Counter()
        for date_str in non_null.astype(str):
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                formats['ISO'] += 1
            elif re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                formats['US'] += 1
            elif re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
                formats['EU'] += 1
            else:
                formats['other'] += 1
        
        if formats:
            most_common_count = formats.most_common(1)[0][1]
            consistency_pct = (most_common_count / len(non_null)) * 100
        else:
            consistency_pct = 0
        
        return {
            'consistency_pct': consistency_pct,
            'formats': dict(formats),
            'recommendation': 'Standardize to ISO format (YYYY-MM-DD)'
        }
    
    def calculate_validity(self) -> Dict:
        """Calculate data validity"""
        validity_checks = {}
        
        # Email validity
        email_cols = [c for c in self.data.columns if 'email' in c.lower()]
        for col in email_cols:
            validity_checks[f'{col}_email'] = self.validate_emails(self.data[col])
        
        # Phone validity
        phone_cols = [c for c in self.data.columns if 'phone' in c.lower()]
        for col in phone_cols:
            validity_checks[f'{col}_phone'] = self.validate_phones(self.data[col])
        
        # Calculate overall validity score
        if validity_checks:
            validity_score = sum(
                v['valid_pct'] for v in validity_checks.values()
            ) / len(validity_checks)
        else:
            validity_score = 100
        
        return {
            'score': validity_score,
            'field_details': validity_checks
        }
    
    def validate_emails(self, series: pd.Series) -> Dict:
        """Validate email addresses"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return {'valid_pct': 100, 'valid_count': 0, 'invalid_count': 0}
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        valid_count = sum(1 for email in non_null.astype(str) if re.match(email_pattern, email))
        
        return {
            'valid_pct': (valid_count / len(non_null)) * 100,
            'valid_count': valid_count,
            'invalid_count': len(non_null) - valid_count
        }
    
    def validate_phones(self, series: pd.Series) -> Dict:
        """Validate phone numbers"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return {'valid_pct': 100, 'valid_count': 0, 'invalid_count': 0}
        
        # Accept various phone formats
        phone_patterns = [
            r'^\d{10}$',
            r'^\d{3}-\d{3}-\d{4}$',
            r'^\(\d{3}\) \d{3}-\d{4}$',
            r'^\+\d{11}$'
        ]
        
        valid_count = 0
        for phone in non_null.astype(str):
            if any(re.match(pattern, phone) for pattern in phone_patterns):
                valid_count += 1
        
        return {
            'valid_pct': (valid_count / len(non_null)) * 100,
            'valid_count': valid_count,
            'invalid_count': len(non_null) - valid_count
        }
    
    def calculate_uniqueness(self) -> Dict:
        """Calculate uniqueness metrics"""
        total_records = len(self.data)
        
        # Exact duplicates
        unique_records = len(self.data.drop_duplicates())
        exact_duplicates = total_records - unique_records
        
        # ID field uniqueness
        id_cols = [c for c in self.data.columns if 'id' in c.lower()]
        id_uniqueness = {}
        for col in id_cols:
            unique_ids = self.data[col].nunique()
            id_uniqueness[col] = {
                'unique_count': unique_ids,
                'duplicate_count': total_records - unique_ids,
                'uniqueness_pct': (unique_ids / total_records) * 100
            }
        
        # Overall uniqueness score
        uniqueness_score = ((total_records - exact_duplicates) / total_records) * 100
        
        return {
            'score': uniqueness_score,
            'total_records': total_records,
            'unique_records': unique_records,
            'exact_duplicates': exact_duplicates,
            'id_uniqueness': id_uniqueness
        }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive quality report"""
        print("Calculating completeness...")
        completeness = self.calculate_completeness()
        
        print("Calculating consistency...")
        consistency = self.calculate_consistency()
        
        print("Calculating validity...")
        validity = self.calculate_validity()
        
        print("Calculating uniqueness...")
        uniqueness = self.calculate_uniqueness()
        
        # Calculate overall quality score
        overall_score = (
            completeness['score'] * 0.40 +
            consistency['score'] * 0.30 +
            validity['score'] * 0.20 +
            uniqueness['score'] * 0.10
        )
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            completeness, consistency, validity, uniqueness
        )
        
        report = {
            'overall_score': round(overall_score, 2),
            'grade': self.get_grade(overall_score),
            'completeness': completeness,
            'consistency': consistency,
            'validity': validity,
            'uniqueness': uniqueness,
            'recommendations': recommendations,
            'metadata': {
                'data_source': self.data_path,
                'total_records': len(self.data),
                'total_fields': len(self.data.columns),
                'fields': list(self.data.columns)
            }
        }
        
        return report
    
    def get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A (Excellent)'
        elif score >= 75:
            return 'B (Good)'
        elif score >= 60:
            return 'C (Fair)'
        elif score >= 40:
            return 'D (Poor)'
        else:
            return 'F (Critical)'
    
    def generate_recommendations(self, completeness, consistency, validity, uniqueness) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Completeness recommendations
        if completeness['score'] < 80:
            incomplete_fields = [
                f for f, details in completeness['field_details'].items()
                if details['non_empty_pct'] < 80
            ]
            recommendations.append(
                f"Improve completeness for fields: {', '.join(incomplete_fields[:5])}"
            )
        
        # Consistency recommendations
        if consistency['score'] < 80:
            recommendations.append(
                "Standardize data formats (phone numbers, dates, addresses)"
            )
        
        # Validity recommendations
        if validity['score'] < 80:
            recommendations.append(
                "Fix invalid data (emails, phone numbers, dates)"
            )
        
        # Uniqueness recommendations
        if uniqueness['score'] < 95:
            recommendations.append(
                f"Remove {uniqueness['exact_duplicates']} duplicate records"
            )
        
        if not recommendations:
            recommendations.append("Data quality is excellent! Ready for entity resolution.")
        
        return recommendations
    
    def save_report(self, output_path: str):
        """Save report to JSON file"""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {output_path}")
        return report
    
    def print_summary(self):
        """Print report summary"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("DATA QUALITY REPORT")
        print("="*60)
        print(f"\nData Source: {report['metadata']['data_source']}")
        print(f"Total Records: {report['metadata']['total_records']:,}")
        print(f"Total Fields: {report['metadata']['total_fields']}")
        
        print(f"\n{'OVERALL QUALITY SCORE':<30} {report['overall_score']:.1f}/100")
        print(f"{'GRADE':<30} {report['grade']}")
        
        print(f"\n{'COMPONENT SCORES':<30}")
        print(f"{'  Completeness (40%)':<30} {report['completeness']['score']:.1f}/100")
        print(f"{'  Consistency (30%)':<30} {report['consistency']['score']:.1f}/100")
        print(f"{'  Validity (20%)':<30} {report['validity']['score']:.1f}/100")
        print(f"{'  Uniqueness (10%)':<30} {report['uniqueness']['score']:.1f}/100")
        
        print(f"\n{'RECOMMENDATIONS':<30}")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_quality_scorer.py <data_file> [output_report.json]")
        sys.exit(1)
    
    data_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'data_quality_report.json'
    
    scorer = DataQualityScorer(data_file)
    scorer.print_summary()
    scorer.save_report(output_file)
```

## Usage

```bash
# Analyze data quality
python src/utils/data_quality_scorer.py data/raw/customers.csv docs/quality_customers.json

# View report
cat docs/quality_customers.json | jq '.overall_score'
```

## Visual Quality Dashboard

Create a simple HTML dashboard:

```python
def generate_html_dashboard(report: Dict, output_path: str):
    """Generate HTML quality dashboard"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Quality Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .score {{ font-size: 48px; font-weight: bold; }}
            .grade-A {{ color: #28a745; }}
            .grade-B {{ color: #5cb85c; }}
            .grade-C {{ color: #ffc107; }}
            .grade-D {{ color: #fd7e14; }}
            .grade-F {{ color: #dc3545; }}
            .metric {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
            .progress-bar {{ 
                width: 100%; 
                height: 30px; 
                background: #f0f0f0; 
                border-radius: 5px;
                overflow: hidden;
            }}
            .progress-fill {{ 
                height: 100%; 
                background: #28a745; 
                transition: width 0.3s;
            }}
        </style>
    </head>
    <body>
        <h1>Data Quality Dashboard</h1>
        <h2>{report['metadata']['data_source']}</h2>
        
        <div class="metric">
            <h3>Overall Quality Score</h3>
            <div class="score grade-{report['grade'][0]}">{report['overall_score']:.1f}/100</div>
            <p>Grade: {report['grade']}</p>
        </div>
        
        <div class="metric">
            <h3>Completeness (40% weight)</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {report['completeness']['score']}%"></div>
            </div>
            <p>{report['completeness']['score']:.1f}%</p>
        </div>
        
        <div class="metric">
            <h3>Consistency (30% weight)</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {report['consistency']['score']}%"></div>
            </div>
            <p>{report['consistency']['score']:.1f}%</p>
        </div>
        
        <div class="metric">
            <h3>Validity (20% weight)</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {report['validity']['score']}%"></div>
            </div>
            <p>{report['validity']['score']:.1f}%</p>
        </div>
        
        <div class="metric">
            <h3>Uniqueness (10% weight)</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {report['uniqueness']['score']}%"></div>
            </div>
            <p>{report['uniqueness']['score']:.1f}%</p>
        </div>
        
        <div class="metric">
            <h3>Recommendations</h3>
            <ul>
                {''.join(f'<li>{rec}</li>' for rec in report['recommendations'])}
            </ul>
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"Dashboard saved to: {output_path}")
```

## Agent Behavior

When a user is in Module 3, the agent should:

1. **Run quality scorer** on each data source
2. **Generate quality report** with scores and metrics
3. **Create HTML dashboard** for visualization
4. **Review scores** with user
5. **Provide recommendations** for improvement
6. **Document quality** in `docs/data_quality_report.md`
7. **Track quality scores** for comparison after mapping

## Output Files

- `docs/data_quality_report.json` - Detailed quality metrics
- `docs/data_quality_dashboard.html` - Visual dashboard
- `docs/data_quality_report.md` - Summary documentation

## Related Documentation

- `POWER.md` - Module 3 overview
- `steering/steering.md` - Module 3 workflow
- `steering/data-quality-scoring.md` - Detailed scoring guide

## Version History

- **v3.0.0** (2026-03-17): Module 3 enhanced with automated quality scoring
