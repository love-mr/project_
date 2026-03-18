# Placeholder for machine learning model
# For now, vaccine assignment is hardcoded in views.assign_vaccine
# Replace this with real model inference logic if needed.

def predict_vaccine(age):
    # stub example similar to assign_vaccine
    if age <= 1:
        return 'HepB'
    elif age <= 2:
        return 'DTaP'
    elif age <= 3:
        return 'Polio'
    elif age <= 4:
        return 'MMR'
    else:
        return 'Varicella'
