## Operational Security Specialization - Process report

Specialization: Operational Security - D
Group: 15 
Name: Ebba Arrhenius Winblad

## Threat modeling
I started by analyzing the deployed application and identified relevant assets, attack surfaces and possible attacker actions.

A STRIDE threat model and risk assessment was created. Attack trees were then used to analyze selected attack scenarios in more detail (see attack trees svg-files). 
The threat modeling process is documented in threat_model.md and the attack trees. 

## Selecting observation point
The threat model was used to decide what security relevant activity needed to be observable. 

Observation points was selected around authentication, documet access, uploads, RMAP authentication, HTTP requests and application/database availabilit. 

## Implementing logging and telemetry
Logging was added to the selected observation points. 
During this process it was important to not include passwords, authentication tokens or other sensitive values in the logs. 

I did a test that reveled that secret document links could appear in the general HTTP logs. I fixed that by changing to redact these paths. 

## Developing detection rules
After finding security events, monitoring rules were implemented to detect patterns such as repeated failed authentication and repeatd denied document access. These rules were implemented in the security_monitoring.py

## Testing
The monitoring was validated using automated tests and controlled security tests. 
Example: Repeated failed login attempts, unauthorized document access and invalid RMAP authenticaation attempts were generated to verify that the expected security alerts were produced. Problems that was discovered during the testing were corrected and then I tested it again. 

## Incident reporing
I uppadate our incident templet. And then documented security events that has happend during the project in the incident journal. 
I found that earlier events were difficult to investiagte when we did have sufficient security telemtry before.

## Result and limitations
The implementation provides logging, detection rules an a basic operator monitoring for several threats identified in the threat model. However, the implemntation still has limitations: in memory monitoring state, limited IP visibility in the docker environment and bounded rather than permanent log retention. 
