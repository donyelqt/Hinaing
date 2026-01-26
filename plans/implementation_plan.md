# Implementation Plan for Analysis Mode Feature

## Overview
This document provides a detailed implementation plan for integrating the new analysis mode feature into the sentiment generator and chat analyzer pipeline. The plan includes frontend changes, backend modifications, and testing strategies.

## Phase 1: Frontend Implementation

### Step 1: Add Mode Selection UI

#### Files to Modify:
1. `frontend/src/features/sentiment/components/sentiment-generator-page.tsx`
2. `frontend/src/features/chat/chat-analyze-page.tsx`

#### Implementation Details:

##### 1. Add Mode Selection Dropdown
```typescript
// Define mode options
type AnalysisMode = 'full' | 'sentiment' | 'epistemic';

const MODE_OPTIONS = [
  { value: 'full', label: 'Full Analysis Mode', description: 'Complete analysis with sentiment, credibility, and thematic insights' },
  { value: 'sentiment', label: 'Sentiment Only', description: 'Focused sentiment analysis only' },
  { value: 'epistemic', label: 'Epistemic Discovery Only', description: 'Focused credibility and thematic analysis' }
];
```

##### 2. Update State Management
```typescript
// Add mode state to useSentimentGenerator hook
const [mode, setMode] = React.useState<AnalysisMode>('full');
```

##### 3. Add UI Component for Mode Selection
```typescript
<div className="space-y-3">
  <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Analysis Mode</span>
  <div className="space-y-2">
    {MODE_OPTIONS.map((option) => (
      <label key={option.value} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm cursor-pointer">
        <input
          type="radio"
          className="mt-1 h-4 w-4 rounded border-slate-300 text-hinaing-blue-500 focus:ring-hinaing-blue-500 focus:ring-offset-2"
          checked={mode === option.value}
          onChange={() => setMode(option.value as AnalysisMode)}
          value={option.value}
        />
        <div>
          <span className="font-medium text-slate-800">{option.label}</span>
          <span className="block text-xs text-slate-500">{option.description}</span>
        </div>
      </label>
    ))}
  </div>
</div>
```

##### 4. Update API Request Payload
```typescript
const payload = {
  platforms: state.platforms,
  time_window: state.timeWindow,
  focus_areas: state.focusAreas,
  include_alerts: state.includeAlerts,
  mode: mode // Add mode to the payload
};
```

### Step 2: Update UI Feedback

#### 1. Visual Indicators
- Add visual indicators to show which mode is selected
- Update the UI to reflect the implications of the selected mode

#### 2. Performance Indicators
- Show estimated processing time for each mode
- Provide feedback on the type of results to expect

## Phase 2: Backend Implementation

### Step 1: Modify API Endpoints

#### Files to Modify:
1. `backend/app/routers/agent.py`
2. `backend/app/routers/chat_analyze.py`

#### Implementation Details:

##### 1. Update Request Schema
```python
from pydantic import BaseModel
from typing import Optional, List

class SnapshotRequest(BaseModel):
    platforms: List[str]
    time_window: str
    focus_areas: List[str]
    include_alerts: bool
    mode: Optional[str] = "full"  # Default to full analysis mode
```

##### 2. Update API Endpoint
```python
@router.post("/insights/snapshot")
async def generate_snapshot(
    request: SnapshotRequest
):
    # Pass the mode to the pipeline
    result = await pipeline.execute(
        platforms=request.platforms,
        time_window=request.time_window,
        focus_areas=request.focus_areas,
        include_alerts=request.include_alerts,
        mode=request.mode
    )
    return result
```

### Step 3: Modify Pipeline Orchestration

#### Files to Modify:
1. `backend/app/services/insights/graph.py`

#### Implementation Details:

##### 1. Update Pipeline Logic
```python
async def execute_pipeline(
    platforms: List[str],
    time_window: str,
    focus_areas: List[str],
    include_alerts: bool,
    mode: str = "full"
):
    # Node 1: Query Orchestrator
    query_plan = await query_orchestrator.run()
    
    # Node 2: Retrieval
    documents = await retrieval_agent.run(query_plan)
    
    # Node 3: Context Augmentation
    enriched_documents = await context_agent.retrieve_knowledge(documents)
    
    # Node 4: Unified Analysis (Conditional based on mode)
    if mode == "full":
        # Execute all agents
        sentiment_results = await sentiment_agent.run(enriched_documents)
        credibility_results = await credibility_agent.run(enriched_documents)
        theme_routed_docs = await theme_router.run(enriched_documents)
        
        # Merge results
        analyzed_documents = merge_results(sentiment_results, credibility_results, theme_routed_docs)
    
    elif mode == "sentiment":
        # Execute sentiment agent only
        sentiment_results = await sentiment_agent.run(enriched_documents)
        analyzed_documents = sentiment_results
    
    elif mode == "epistemic":
        # Execute credibility and theme router agents
        credibility_results = await credibility_agent.run(enriched_documents)
        theme_routed_docs = await theme_router.run(enriched_documents)
        
        # Merge results
        analyzed_documents = merge_results(credibility_results, theme_routed_docs)
    
    # Node 5: Memory Consolidation (Conditional based on mode)
    if mode in ["full", "epistemic"]:
        await context_agent.consolidate_memory(analyzed_documents)
    
    # Node 6: Theme Agents (Conditional based on mode)
    if mode in ["full", "epistemic"]:
        theme_insights = await execute_theme_agents(theme_routed_docs)
    else:
        theme_insights = []
    
    # Node 7: Coordinator
    final_result = await coordinator_agent.run(
        documents=analyzed_documents,
        theme_insights=theme_insights,
        mode=mode
    )
    
    return final_result
```

### Step 4: Update Agents for Partial Execution

#### Files to Modify:
1. `backend/app/services/agents/sentiment_agent.py`
2. `backend/app/services/agents/credibility_agent.py`
3. `backend/app/services/agents/theme_router_agent.py`
4. `backend/app/services/agents/coordinator_agent.py`

#### Implementation Details:

##### 1. Sentiment Agent
```python
class SentimentAgent:
    async def run(self, documents: List[Document]) -> List[Document]:
        # Ensure the agent can operate independently
        results = []
        for doc in documents:
            sentiment = await self.analyze_sentiment(doc)
            doc.metadata["sentiment"] = sentiment
            results.append(doc)
        return results
```

##### 2. Credibility Agent
```python
class CredibilityAgent:
    async def run(self, documents: List[Document]) -> List[Document]:
        # Ensure the agent can operate independently
        results = []
        for doc in documents:
            credibility = await self.analyze_credibility(doc)
            doc.metadata["credibility"] = credibility
            results.append(doc)
        return results
```

##### 3. Theme Router Agent
```python
class ThemeRouterAgent:
    async def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        # Ensure the agent can operate independently
        routed_docs = {}
        for doc in documents:
            theme = await self.determine_theme(doc)
            if theme not in routed_docs:
                routed_docs[theme] = []
            routed_docs[theme].append(doc)
        return routed_docs
```

##### 4. Coordinator Agent
```python
class CoordinatorAgent:
    async def run(
        self,
        documents: List[Document],
        theme_insights: List[Insight],
        mode: str = "full"
    ) -> SnapshotResponse:
        # Handle partial results based on mode
        if mode == "full":
            # Generate comprehensive narrative
            narrative = await self.generate_comprehensive_narrative(documents, theme_insights)
        elif mode == "sentiment":
            # Generate sentiment-focused narrative
            narrative = await self.generate_sentiment_narrative(documents)
        elif mode == "epistemic":
            # Generate credibility and thematic narrative
            narrative = await self.generate_epistemic_narrative(documents, theme_insights)
        
        return SnapshotResponse(
            overall_sentiment=narrative.overall_sentiment,
            actionable_insights=narrative.insights,
            sources=narrative.sources,
            alerts=narrative.alerts
        )
```

## Phase 3: Testing and Validation

### Step 1: Unit Testing

#### Files to Create:
1. `backend/tests/test_analysis_modes.py`

#### Implementation Details:

##### 1. Test Mode Selection
```python
def test_mode_selection():
    # Test that mode selection is correctly passed to the pipeline
    request = SnapshotRequest(
        platforms=["web"],
        time_window="24h",
        focus_areas=["infrastructure"],
        include_alerts=True,
        mode="sentiment"
    )
    assert request.mode == "sentiment"
```

##### 2. Test Pipeline Execution
```python
@pytest.mark.asyncio
async def test_pipeline_execution():
    # Test that the pipeline executes correctly for each mode
    result = await execute_pipeline(
        platforms=["web"],
        time_window="24h",
        focus_areas=["infrastructure"],
        include_alerts=True,
        mode="sentiment"
    )
    assert result is not None
    assert "overall_sentiment" in result
```

### Step 2: Integration Testing

#### Files to Create:
1. `backend/tests/test_integration.py`

#### Implementation Details:

##### 1. Test Full Pipeline
```python
@pytest.mark.asyncio
async def test_full_pipeline():
    # Test the full pipeline with all modes
    for mode in ["full", "sentiment", "epistemic"]:
        result = await execute_pipeline(
            platforms=["web"],
            time_window="24h",
            focus_areas=["infrastructure"],
            include_alerts=True,
            mode=mode
        )
        assert result is not None
        assert "overall_sentiment" in result
```

### Step 3: User Acceptance Testing

#### Implementation Details:

##### 1. Test UI/UX
- Verify that the mode selection dropdown is intuitive and easy to use
- Ensure that the UI provides clear feedback on the selected mode
- Confirm that the performance indicators are accurate and helpful

##### 2. Test Results
- Verify that the results are accurate and relevant to the selected mode
- Ensure that the results are displayed correctly in the UI
- Confirm that the results meet user expectations for each mode

## Phase 4: Deployment

### Step 1: Backend Deployment

#### Implementation Details:

##### 1. Deploy Backend Changes
- Deploy the modified API endpoints and pipeline logic
- Ensure that the backend is running smoothly and handling requests correctly

##### 2. Monitor Performance
- Monitor the backend performance to ensure that the new modes are executing efficiently
- Log any issues or errors for quick resolution

### Step 2: Frontend Deployment

#### Implementation Details:

##### 1. Deploy Frontend Changes
- Deploy the updated UI components and state management
- Ensure that the frontend is interacting correctly with the backend

##### 2. Monitor User Feedback
- Gather user feedback on the new feature
- Address any issues or concerns raised by users

## Rollback Plan

### Step 1: Maintain Backward Compatibility
- Ensure that the existing API endpoints continue to work without the mode parameter
- Provide a fallback mechanism to default behavior in case of issues

### Step 2: Monitor System Logs
- Monitor system logs for any errors or issues
- Address any issues promptly to minimize downtime

### Step 3: User Communication
- Communicate any changes or issues to users promptly
- Provide clear instructions on how to use the new feature

## Conclusion
This implementation plan outlines a clear path to integrating the new analysis mode feature into the sentiment generator and chat analyzer pipeline. By following this plan, we can ensure a smooth and successful implementation that meets user needs and expectations.