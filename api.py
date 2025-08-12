from itertools import count
from typing import List, Dict, Optional, Tuple
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# CURRENT ACTIVE API VERSION

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:10080",
    "http://127.0.0.1",
    "http://127.0.0.1:10080",
    "http://0.0.0.0:10000",
    "https://blogic-0d9z.onrender.com/"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app = FastAPI()

# origins = [
#     "http://localhost",
#     "http://localhost:8080",  # Add your frontend's origin
#     "http://127.0.0.1",
#     "http://127.0.0.1:8080",  # Add your frontend's origin
#     "http://0.0.0.0:8000",  # Add your frontend's origin
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows all origins for development
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods
#     allow_headers=["*"],  # Allows all headers
# )

# Models 
class CoSigner(BaseModel):
    CO_SIGNER_NAME_FROM_APS: str
    CO_SIGNER_NAME_FROM_ID: str
    CO_SIGNER_ADDRESS_FROM_APS: str
    CO_SIGNER_ADDRESS_LIST_FROM_LANDREGISTRY: List[str]
    CO_SIGNER_ALL_PROPERTIES_PURCHASE_PRICE_FROM_LANDREGISTRY: List[float]
    CO_SIGNER_ALL_PROPERTIES_VALUE_FROM_AVM: List[float]
    CO_SIGNER_ALL_PROPERTIES_TOTAL_DEBT_FROM_PURVIEW: List[float]
    CO_SIGNER_ALL_PROPERTIES_EQUITY: List[float]

class BuyerData(BaseModel):
    PURCHASER_NAME_FROM_APS: str
    PURCHASER_NAME_FROM_ID: str
    PURCHASER_NAME_FROM_HOUSESIGMA: Optional[str] = ""
    PURCHASER_ADDRESS_FROM_APS: str
    PURCHASER_ADDRESS_FROM_ID: str
    PURCHASER_ADDRESS_LIST_FROM_LANDREGISTRY: List[str]
    PURCHASER_AGE_FROM_ID: int
    PURCHASER_ALL_PROPERTIES_PURCHASE_PRICE_FROM_LANDREGISTRY: List[float]
    PURCHASER_ALL_PROPERTIES_VALUE_FROM_AVM: List[float]
    PURCHASER_ALL_PROPERTIES_TOTAL_DEBT_FROM_PURVIEW: List[float]
    PURCHASER_ALL_PROPERTIES_EQUITY: List[float]
    PURCHASER_DEPOSIT_PAID_FROM_APS: float
    PURCHASER_ID_ISSUE_DATE: str
    PURCHASER_DRIVER_LICENSE_TYPE: str
    CO_SIGNER_LIST_FROM_APS: List[CoSigner]
    DISTANCE: float
    PRIMARY_RESIDENCE_PURCHASE_PRICE_FROM_LANDREGISTRY: float
    PRIMARY_RESIDENCE_VALUE_FROM_AVM: float
    PRIMARY_RESIDENCE_TOTAL_DEBT_FROM_PURVIEW: float
    PRIMARY_RESIDENCE_EQUITY: float
    PRIMARY_RESIDENCE_TITLE_NAMES: List[str]
    PROPERTY_PRICE: float
    OTHER_DEPOSIT_PAID_NAME_LIST_FROM_APS: List[str]
    MORTGAGE_APPROVAL: bool
    MORTGAGE_APPROVAL_NAMES: List[str]

class BuyerRiskAssessor:
    def __init__(self):
        self.NO_RISK = "No Risk"
        self.VERY_LOW = "Very Low"
        self.LOW = "Low"
        self.MEDIUM = "Medium"
        self.HIGH = "High"
        self.VERY_HIGH = "Very High"
        self.REASONS = []
    
    def assess_buyer_risk(self, buyer_data: Dict) -> Dict:
        """Main assessment function using your exact data structure"""
        risk_level = self.HIGH
        actions = []
        self.REASONS = []

        # Check home ownership using your variables
        owns_home = self._check_ownership(buyer_data)
        
        if not owns_home:
            risk_level, actions = self._assess_non_homeowner(buyer_data)
        else:
            risk_level, actions = self._assess_homeowner(buyer_data)

        # Apply all general checks
        risk_level = self._apply_general_checks(buyer_data, risk_level, actions)
        
        return {
            "risk_level": risk_level,
            "suggested_actions": actions,
            "risk_factors": self._get_risk_factors(buyer_data),
            "reasons": self.REASONS
        }
    # -----------------------------------------------------------------------
    
    def _check_ownership(self, buyer_data: Dict) -> bool:
        """Check ownership using your exact variable names"""
        # Check primary residence
        if buyer_data.get("PRIMARY_RESIDENCE_TITLE_NAMES"):
            return True
        
        # Check other properties
        if buyer_data.get("PURCHASER_ADDRESS_LIST_FROM_LANDREGISTRY"):
            return True
        
        # Check co-signers' properties
        for cosigner in buyer_data.get("CO_SIGNER_LIST_FROM_APS", []):
            if cosigner.get("CO_SIGNER_ADDRESS_LIST_FROM_LANDREGISTRY"):
                return True
        return False
    
    def _assess_non_homeowner(self, buyer_data: Dict) -> Tuple[str, List[str]]:
        """Assess non-homeowners with your data structure"""
        risk_level = self.NO_RISK
        actions = []
        price = buyer_data.get("PROPERTY_PRICE", 0)
        deposit = buyer_data.get("PURCHASER_DEPOSIT_PAID_FROM_APS", 0)
        deposit_pct = (deposit / price) * 100 if price > 0 else 0
        
        # Price tier checks (Conditions 1-4)
        if price < 800000:
            if deposit_pct > 25:
                risk_level = self.LOW
            elif deposit_pct > 15:
                risk_level = self.MEDIUM
        elif 800000 <= price <= 1000000:
            if deposit_pct > 20:
                risk_level = self.MEDIUM
        elif 1000000 < price <= 1500000:
            if deposit_pct > 25:
                risk_level = self.MEDIUM
        elif price > 1500000:
            if deposit_pct > 25:
                risk_level = self.MEDIUM

        # Override conditions
        if self._has_high_risk_overrides(buyer_data):
            risk_level = self.HIGH

        # Related parties check
        if self._has_related_parties_not_on_aps(buyer_data):
            risk_level = self._increase_risk(risk_level, 1)
            if price > 1000000:
                risk_level = self._increase_risk(risk_level, 2)
            actions.append("Add related parties to APS")

        # Young buyer check
        if (buyer_data.get("PURCHASER_AGE_FROM_ID", 100) < 30 and 
            not self._is_buyer_on_primary_residence_title(buyer_data)):
            actions.append("Request to add co-signers")

        actions.append("Request 25% downpayment proof")
        return risk_level, actions

    def _assess_homeowner(self, buyer_data: Dict) -> Tuple[str, List[str]]:
        """Assess homeowners with your data structure"""
        risk_level = self.MEDIUM
        actions = []
        price = buyer_data.get("PROPERTY_PRICE", 1)
        home_value = buyer_data.get("PRIMARY_RESIDENCE_VALUE_FROM_AVM", 0)
        equity = buyer_data.get("PRIMARY_RESIDENCE_EQUITY", 0)
        equity_pct = (equity / price) * 100 if price > 0 else 0
        
        # Home value to price ratio
        if home_value >= 0.75 * price:
            risk_level = self.LOW
        elif 0.6 * price <= home_value < 0.75 * price:
            risk_level = self.MEDIUM
        else:
            risk_level = self.HIGH

        # Equity checks
        if equity_pct < 5:
            risk_level = self.VERY_HIGH
            self.REASONS.append("Very low equity (<5%)")
        elif equity_pct < 15:
            risk_level = self._increase_risk(risk_level, 2)
            self.REASONS.append("Low equity (5-15%)")
        elif equity_pct < 25:
            risk_level = self._increase_risk(risk_level, 1)
            self.REASONS.append("Moderate equity (15-25%)")

        # Related parties check
        if self._has_related_parties_not_on_aps(buyer_data):
            risk_level = self._increase_risk(risk_level, 1)
            # if price > 1000000:
            risk_level = self._increase_risk(risk_level, 2)
            self.REASONS.append("Same last name different addresses.")
            actions.append("Add related parties to APS")

        # Missing co-owner check
        if self._is_missing_coowner_on_aps(buyer_data):
            risk_level = self._increase_risk(risk_level, 2)
            self.REASONS.append("Missing co-owner on APS")

        actions.append("Verify property ownership and equity")
        return risk_level, actions

    def _apply_general_checks(self, buyer_data: Dict, current_risk: str, actions: List[str]) -> str:
        """Apply all general checks with your exact variables"""
        risk_level = current_risk
        
        if (buyer_data.get("PURCHASER_NAME_FROM_APS") !=
            buyer_data.get("PURCHASER_NAME_FROM_ID")):
            risk_level = self.VERY_HIGH
            self.REASONS.append("Name mismatch between ID and APS")
            
        if (buyer_data.get("PURCHASER_NAME_FROM_APS") !=
            buyer_data.get("PURCHASER_NAME_FROM_HOUSESIGMA")):
            risk_level = self.VERY_HIGH
            self.REASONS.append("Name mismatch between APS and HOUSESIGMA")

        if (buyer_data.get("PURCHASER_NAME_FROM_ID") !=
            buyer_data.get("PURCHASER_NAME_FROM_HOUSESIGMA")):
            risk_level = self.VERY_HIGH
            self.REASONS.append("Name mismatch between ID and HOUSESIGMA")
            
        # Address consistency
        if (buyer_data.get("PURCHASER_ADDRESS_FROM_ID") != 
            buyer_data.get("PURCHASER_ADDRESS_FROM_APS")):
            risk_level = self.VERY_HIGH
            self.REASONS.append("Address mismatch between ID and APS")

        if (buyer_data.get("PURCHASER_ADDRESS_FROM_APS") not in 
            buyer_data.get("PURCHASER_ADDRESS_LIST_FROM_LANDREGISTRY")):
                if buyer_data.get("PURCHASER_ADDRESS_LIST_FROM_LANDREGISTRY"):
                    self.REASONS.append("Address mismatch APS and LAND REGISTRY")
                else:
                    self.REASONS.append("Address in APS not found in LAND REGISTRY - empty")
                    
                risk_level = self.VERY_HIGH
                
        # Distance check
        if buyer_data.get("DISTANCE", 0) > 75:
            risk_level = self._increase_risk(risk_level, 1)
            self.REASONS.append("Long distance (>75km)")

        # Deposit paid by others
        deposit_parties = buyer_data.get("OTHER_DEPOSIT_PAID_NAME_LIST_FROM_APS", [])
        purchaser_name = buyer_data.get("PURCHASER_NAME_FROM_APS")
        if len(deposit_parties) != 1 or purchaser_name not in deposit_parties:
            risk_level = self.VERY_HIGH
            self.REASONS.append("Deposit paid by others")

        # Mortgage approval parties
        mortgage_names = buyer_data.get("MORTGAGE_APPROVAL_NAMES", [])
        if len(mortgage_names) > 1 or purchaser_name not in mortgage_names:
            risk_level = self._increase_risk(risk_level, 1)
            self.REASONS.append("Multiple mortgage parties")

        # Age check
        age = buyer_data.get("PURCHASER_AGE_FROM_ID")
        if age and (age < 30 or age > 60):
            risk_level = self._increase_risk(risk_level, 1)
            self.REASONS.append(f"Age risk ({age} years)")

        # Multiple properties check
        if len(buyer_data.get("PURCHASER_ALL_PROPERTIES_VALUE_FROM_AVM", [])) > 1:
            risk_level = self._increase_risk(risk_level, 1)
            self.REASONS.append("Multiple property ownership")

        # def _has_related_parties_not_on_aps(self, buyer_data: Dict) -> bool:
        #     """Check for related parties not on APS (Suggested Actions 1)"""
        #     # Check if buyer lives at address owned by same last name but not on APS
        #     purchaser_last_name = buyer_data.get("PURCHASER_NAME_FROM_APS", "").split()[-1]
        #     owner_names = buyer_data.get("PRIMARY_RESIDENCE_TITLE_NAMES", [])
            
        #     # Check if any owner has same last name but not on APS
        #     return any(
        #         name.split()[-1] == purchaser_last_name and 
        #         name not in buyer_data.get("APS_NAMES", [])
        #         for name in owner_names
        #     )



        return risk_level

    def _has_high_risk_overrides(self, buyer_data: Dict) -> bool:
        """Check high risk override conditions"""
        # Distance >75km
        if buyer_data.get("DISTANCE", 0) > 75:
            return True
        
        # Deposit paid by others
        deposit_parties = buyer_data.get("OTHER_DEPOSIT_PAID_NAME_LIST_FROM_APS", [])
        purchaser_name = buyer_data.get("PURCHASER_NAME_FROM_APS")
        if len(deposit_parties) != 1 or purchaser_name not in deposit_parties:
            return True

        # Mortgage approval has more parties
        mortgage_names = buyer_data.get("MORTGAGE_APPROVAL_NAMES", [])
        if len(mortgage_names) > 1 or purchaser_name not in mortgage_names:
            return True
        
        # Age <30 or >60
        age = buyer_data.get("PURCHASER_AGE_FROM_ID")
        if age and (age < 30 or age > 60):
            return True
        
        # Different addresses
        if self._has_different_addresses(buyer_data):
            return True
        
        return False

    def _is_buyer_on_primary_residence_title(self, buyer_data: Dict) -> bool:
        """Check if buyer is on primary residence title"""
        return buyer_data.get("PURCHASER_NAME_FROM_APS") in buyer_data.get("PRIMARY_RESIDENCE_TITLE_NAMES", [])
    
    def _has_related_parties_not_on_aps(self, buyer_data: Dict) -> bool:
        """Check for related parties not on APS"""
        purchaser_last_name = buyer_data.get("PURCHASER_NAME_FROM_APS", "").split()[-1]
        owner_names = buyer_data.get("PRIMARY_RESIDENCE_TITLE_NAMES", [])
        
        return any(
            name.split()[-1] == purchaser_last_name and 
            name not in [buyer_data.get("PURCHASER_NAME_FROM_APS")] + 
            [c["CO_SIGNER_NAME_FROM_APS"] for c in buyer_data.get("CO_SIGNER_LIST_FROM_APS", [])]
            for name in owner_names
        )
    
    def _is_missing_coowner_on_aps(self, buyer_data: Dict) -> bool:
        """Check if co-owner is missing from APS"""
        primary_owners = buyer_data.get("PRIMARY_RESIDENCE_TITLE_NAMES", [])
        aps_names = [buyer_data.get("PURCHASER_NAME_FROM_APS")] + \
                   [c["CO_SIGNER_NAME_FROM_APS"] for c in buyer_data.get("CO_SIGNER_LIST_FROM_APS", [])]
        return any(owner not in aps_names for owner in primary_owners)
    
    def _has_different_addresses(self, buyer_data: Dict) -> bool:
        """Check for different addresses"""
        return (buyer_data.get("PURCHASER_ADDRESS_FROM_ID") != 
                buyer_data.get("PURCHASER_ADDRESS_FROM_APS"))
    
    def _has_multiple_buyers_different_addresses(self, buyer_data: Dict) -> bool:
        """Check for multiple buyers with different addresses"""
        aps_names = [buyer_data.get("PURCHASER_NAME_FROM_APS")] + \
                   [c["CO_SIGNER_NAME_FROM_APS"] for c in buyer_data.get("CO_SIGNER_LIST_FROM_APS", [])]
        if len(aps_names) <= 1:
            return False
        
        addresses = set()
        if buyer_data.get("PURCHASER_ADDRESS_FROM_ID"):
            addresses.add(buyer_data["PURCHASER_ADDRESS_FROM_ID"])
        if buyer_data.get("PURCHASER_ADDRESS_FROM_APS"):
            addresses.add(buyer_data["PURCHASER_ADDRESS_FROM_APS"])
        
        for cosigner in buyer_data.get("CO_SIGNER_LIST_FROM_APS", []):
            if cosigner.get("CO_SIGNER_ADDRESS_FROM_APS"):
                addresses.add(cosigner["CO_SIGNER_ADDRESS_FROM_APS"])
        
        return len(addresses) > 1

    def _increase_risk(self, current_risk: str, levels: int = 1) -> str:
        """Increase risk level"""
        risk_order = [self.VERY_LOW, self.LOW, self.MEDIUM, self.HIGH, self.VERY_HIGH]
        try:
            current_index = risk_order.index(current_risk)
            new_index = min(current_index + levels, len(risk_order) - 1)
            return risk_order[new_index]
        except ValueError:
            return current_risk

    def _get_risk_factors(self, buyer_data: Dict) -> List[str]:
        """Generate risk factors list"""
        factors = []
        
        # Ownership status
        if not self._check_ownership(buyer_data):
            factors.append("First-time homebuyer")
        else:
            factors.append("Existing property owner")

        # Property value ratio
        home_value = buyer_data.get("PRIMARY_RESIDENCE_VALUE_FROM_AVM", 0)
        price = buyer_data.get("PROPERTY_PRICE", 1)
        factors.append(f"Home value to price ratio: {home_value/price:.1%}")

        # Deposit percentage
        deposit_pct = buyer_data.get("PURCHASER_DEPOSIT_PAID_FROM_APS", 0) / price * 100
        factors.append(f"Deposit:{float(deposit_pct)}")

        # Distance
        if buyer_data.get("DISTANCE", 0) > 75:
            factors.append(f"Long distance ({buyer_data['DISTANCE']}km)")

        # Age
        age = buyer_data.get("PURCHASER_AGE_FROM_ID")
        if age and (age < 30 or age > 60):
            factors.append(f"Age risk factor ({age} years)")

        return factors

if __name__ == "__main__":
    buyer_data = {
        "PURCHASER_NAME_FROM_APS": "John Smith",
        "PURCHASER_NAME_FROM_ID": "John Smith",
        "PURCHASER_NAME_FROM_HOUSESIGMA": "",
        "PURCHASER_ADDRESS_FROM_APS": "123 Main St, Toronto, ON",
        "PURCHASER_ADDRESS_FROM_ID": "123 Main St, Toronto, ON",
        "PURCHASER_ADDRESS_LIST_FROM_LANDREGISTRY": ["124 Main St, Toronto, ON"],
        "PURCHASER_AGE_FROM_ID": 40,
        "PURCHASER_ALL_PROPERTIES_PURCHASE_PRICE_FROM_LANDREGISTRY": [500000],
        "PURCHASER_ALL_PROPERTIES_VALUE_FROM_AVM": [750000],
        "PURCHASER_ALL_PROPERTIES_TOTAL_DEBT_FROM_PURVIEW": [300000],
        "PURCHASER_ALL_PROPERTIES_EQUITY": [400000],
        "PURCHASER_DEPOSIT_PAID_FROM_APS": 200000,
        "PURCHASER_ID_ISSUE_DATE": "2023-01-01", # implement check 2 years High
        "PURCHASER_DRIVER_LICENSE_TYPE": "Ontario",
        "CO_SIGNER_LIST_FROM_APS": [
            # {
            #     "CO_SIGNER_NAME_FROM_APS": "Jane Smith",
            #     "CO_SIGNER_NAME_FROM_ID": "Jane Smith",
            #     "CO_SIGNER_ADDRESS_FROM_APS": "123 Main St, Toronto, ON",
            #     "CO_SIGNER_ADDRESS_LIST_FROM_LANDREGISTRY": ["124 Main St, Toronto, ON"], # DO We CHECK ADDRESS FOR EACH CO TOO?
            #     "CO_SIGNER_ALL_PROPERTIES_PURCHASE_PRICE_FROM_LANDREGISTRY": [500000],
            #     "CO_SIGNER_ALL_PROPERTIES_VALUE_FROM_AVM": [750000],
            #     "CO_SIGNER_ALL_PROPERTIES_TOTAL_DEBT_FROM_PURVIEW": [300000],
            #     "CO_SIGNER_ALL_PROPERTIES_EQUITY": [400000]
            # }
        ],
        "DISTANCE": 50,
        "PRIMARY_RESIDENCE_PURCHASE_PRICE_FROM_LANDREGISTRY": 500000,
        "PRIMARY_RESIDENCE_VALUE_FROM_AVM": 750000,
        "PRIMARY_RESIDENCE_TOTAL_DEBT_FROM_PURVIEW": 300000,
        "PRIMARY_RESIDENCE_EQUITY": 450000,
        "PRIMARY_RESIDENCE_TITLE_NAMES": ["Jane"],
        "PROPERTY_PRICE": 800000,
        "OTHER_DEPOSIT_PAID_NAME_LIST_FROM_APS": ["Jane"],
        "MORTGAGE_APPROVAL": True,
        "MORTGAGE_APPROVAL_NAMES": ["Jane"],
    }

assessor = BuyerRiskAssessor()


@app.options("/assess-risk")
async def options_assess_risk():
    return {"message": "OK"}


# API endpoint
@app.post("/assess-risk")

async def assess_risk(buyer_data: BuyerData):
    try:
        print("Received data:", buyer_data.dict())  # Log incoming data
        buyer_data_dict = buyer_data.dict()
        result = assessor.assess_buyer_risk(buyer_data_dict)

        print("2. Assessment result:", result)  # Debug log 2
        
        return {
            "success": True,
            "risk_assessment": result,
            "debug": {
                "input_data": buyer_data_dict,
                "assessment_result": result
            }
        }
    except Exception as e:
        print("Error:", str(e))  # Log errors
        return {
            "success": False,
            "error": str(e)
        }



    
  
