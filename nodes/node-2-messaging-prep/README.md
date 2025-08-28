# Node 2: Messaging Prep (Cold + BIT + Doc)

## Scope
This node handles message preparation and campaign strategy:
- Cold outreach sequencing
- BIT (Behavior, Interest, Timing) classification
- Doctrine management and compliance
- Template generation and personalization

## Acceptance Checklist

### BIT (Behavior, Interest, Timing)
- [ ] Behavior scoring algorithm
- [ ] Interest level classification
- [ ] Timing optimization engine
- [ ] Lead segmentation by BIT scores
- [ ] Dynamic tag assignment
- [ ] Priority queue management
- [ ] A/B testing framework for BIT parameters

### Doctrine
- [ ] Campaign strategy definitions
- [ ] Altitude mapping (40k, 30k, 20k, 10k, 5k views)
- [ ] Compliance rule engine
- [ ] Message governance policies
- [ ] Channel selection logic
- [ ] Frequency capping rules
- [ ] Suppression list management

### Cold Outreach
- [ ] Sequence builder (1-7 touch cadence)
- [ ] Sniper vs Broad campaign modes
- [ ] Personalization engine
- [ ] Follow-up automation rules
- [ ] Response detection logic
- [ ] Opt-out handling
- [ ] Warm-up sequences for new domains

### Templates
- [ ] Email template library
- [ ] LinkedIn message templates
- [ ] X (Twitter) DM templates
- [ ] Variable substitution engine
- [ ] Template validation
- [ ] Liquid/Handlebars support
- [ ] Preview generation

## Folder Structure
```
node-2-messaging-prep/
├── bit/             # BIT classification and scoring
├── doctrine/        # Campaign strategy and compliance
├── cold/            # Cold outreach sequencing
└── templates/       # Message templates and personalization
```

## Dependencies
- Liquid or Handlebars for templating
- Natural language processing for personalization
- Campaign scheduling engine
- A/B testing framework

## API Contracts
- POST /api/bit/classify
- GET /api/doctrine/strategy
- POST /api/cold/sequence
- POST /api/templates/render