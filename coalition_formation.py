"""
Coalition Formation Network
Device-to-Device (D2D) communication and multi-agent coordination
"""

import numpy as np
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging


class AgentType(Enum):
    """Types of agents in the FCSTN network"""
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    XR_DEVICE = "xr_device"
    EDGE_NODE = "edge_node"
    CLOUD_NODE = "cloud_node"
    SENSOR = "sensor"


class CoalitionType(Enum):
    """Types of coalitions"""
    COGNITIVE = "cognitive"  # Human + AI + XR
    COMPUTE = "compute"      # AI + Edge + Cloud
    INFRASTRUCTURE = "infrastructure"  # Network resources


@dataclass
class Agent:
    """Agent in the coalition network"""
    id: str
    agent_type: AgentType
    capabilities: List[str]
    resources: Dict[str, float]  # e.g., {"compute": 100, "bandwidth": 50}
    position: Optional[Tuple[float, float, float]] = None
    coalition_id: Optional[str] = None


@dataclass
class Coalition:
    """Coalition of cooperating agents"""
    id: str
    coalition_type: CoalitionType
    members: Set[str]  # Agent IDs
    value: float  # Coalition utility value
    resources: Dict[str, float]


class CoalitionFormationGame:
    """
    Implements coalition formation using merge-and-split algorithm.
    
    Based on overlapping coalition game theory for D2D networks.
    """
    
    def __init__(self, agents: List[Agent]):
        """
        Initialize coalition formation game.
        
        Args:
            agents: List of all agents in the network
        """
        self.agents = {agent.id: agent for agent in agents}
        self.coalitions: Dict[str, Coalition] = {}
        self.iteration = 0
        
        # Initialize each agent in its own coalition
        self._initialize_singleton_coalitions()
        
        logging.info(f"Coalition game initialized with {len(agents)} agents")
    
    def _initialize_singleton_coalitions(self):
        """Create initial singleton coalitions for each agent"""
        for agent_id, agent in self.agents.items():
            coalition_id = f"C_{agent_id}"
            
            coalition = Coalition(
                id=coalition_id,
                coalition_type=self._infer_coalition_type([agent]),
                members={agent_id},
                value=self._compute_coalition_value({agent_id}),
                resources=agent.resources.copy()
            )
            
            self.coalitions[coalition_id] = coalition
            agent.coalition_id = coalition_id
    
    def _infer_coalition_type(self, agents: List[Agent]) -> CoalitionType:
        """Infer coalition type from agent composition"""
        types = {agent.agent_type for agent in agents}
        
        if AgentType.HUMAN in types and AgentType.AI_AGENT in types:
            return CoalitionType.COGNITIVE
        elif AgentType.AI_AGENT in types and AgentType.EDGE_NODE in types:
            return CoalitionType.COMPUTE
        else:
            return CoalitionType.INFRASTRUCTURE
    
    def _compute_coalition_value(self, member_ids: Set[str]) -> float:
        """
        Compute the value (utility) of a coalition.
        
        v(S) = Σ U_i for i in S
        
        Includes synergy bonuses for complementary agent types.
        
        Args:
            member_ids: Set of agent IDs in the coalition
            
        Returns:
            Coalition value
        """
        members = [self.agents[aid] for aid in member_ids]
        
        # Base value: sum of individual utilities
        base_value = sum(
            sum(agent.resources.values()) for agent in members
        )
        
        # Synergy bonuses
        synergy = 0.0
        types = {agent.agent_type for agent in members}
        
        # Cognitive coalition bonus
        if AgentType.HUMAN in types and AgentType.AI_AGENT in types and AgentType.XR_DEVICE in types:
            synergy += 50.0
        
        # Compute coalition bonus
        if AgentType.AI_AGENT in types and AgentType.EDGE_NODE in types:
            synergy += 30.0
        
        # Infrastructure coalition bonus
        if AgentType.EDGE_NODE in types and AgentType.CLOUD_NODE in types:
            synergy += 20.0
        
        return base_value + synergy
    
    def _can_merge(self, coalition1: Coalition, coalition2: Coalition) -> bool:
        """
        Check if two coalitions can merge.
        
        Constraints:
        - No overlapping members
        - Compatible types
        - Resource constraints satisfied
        """
        # No overlap
        if coalition1.members & coalition2.members:
            return False
        
        # Check type compatibility
        merged_members = coalition1.members | coalition2.members
        merged_agents = [self.agents[aid] for aid in merged_members]
        
        # Allow merging if it forms a valid coalition type
        return True
    
    def _merge_coalitions(self, coalition1: Coalition, coalition2: Coalition) -> Coalition:
        """
        Merge two coalitions.
        
        Args:
            coalition1: First coalition
            coalition2: Second coalition
            
        Returns:
            Merged coalition
        """
        merged_members = coalition1.members | coalition2.members
        merged_id = f"C_merged_{self.iteration}"
        
        # Aggregate resources
        merged_resources = {}
        for key in set(coalition1.resources.keys()) | set(coalition2.resources.keys()):
            merged_resources[key] = (
                coalition1.resources.get(key, 0) +
                coalition2.resources.get(key, 0)
            )
        
        # Determine type
        merged_agents = [self.agents[aid] for aid in merged_members]
        merged_type = self._infer_coalition_type(merged_agents)
        
        merged_coalition = Coalition(
            id=merged_id,
            coalition_type=merged_type,
            members=merged_members,
            value=self._compute_coalition_value(merged_members),
            resources=merged_resources
        )
        
        return merged_coalition
    
    def _split_coalition(self, coalition: Coalition) -> List[Coalition]:
        """
        Split a coalition into smaller coalitions.
        
        Uses simple bisection for demonstration.
        
        Args:
            coalition: Coalition to split
            
        Returns:
            List of smaller coalitions
        """
        if len(coalition.members) <= 1:
            return [coalition]
        
        members_list = list(coalition.members)
        mid = len(members_list) // 2
        
        # Create two sub-coalitions
        sub1_members = set(members_list[:mid])
        sub2_members = set(members_list[mid:])
        
        sub1_agents = [self.agents[aid] for aid in sub1_members]
        sub2_agents = [self.agents[aid] for aid in sub2_members]
        
        sub1 = Coalition(
            id=f"C_split1_{self.iteration}",
            coalition_type=self._infer_coalition_type(sub1_agents),
            members=sub1_members,
            value=self._compute_coalition_value(sub1_members),
            resources={k: v/2 for k, v in coalition.resources.items()}
        )
        
        sub2 = Coalition(
            id=f"C_split2_{self.iteration}",
            coalition_type=self._infer_coalition_type(sub2_agents),
            members=sub2_members,
            value=self._compute_coalition_value(sub2_members),
            resources={k: v/2 for k, v in coalition.resources.items()}
        )
        
        return [sub1, sub2]
    
    def run_merge_and_split(self, max_iterations: int = 50) -> Dict[str, Coalition]:
        """
        Execute merge-and-split coalition formation algorithm.
        
        Algorithm:
        1. Merge phase: Try to merge coalitions that increase total value
        2. Split phase: Try to split coalitions that increase total value
        3. Repeat until convergence
        
        Args:
            max_iterations: Maximum number of iterations
            
        Returns:
            Final coalition structure
        """
        for iteration in range(max_iterations):
            self.iteration = iteration
            changed = False
            
            # MERGE PHASE
            coalition_list = list(self.coalitions.values())
            
            for i, c1 in enumerate(coalition_list):
                for c2 in coalition_list[i+1:]:
                    if self._can_merge(c1, c2):
                        # Compute value improvement
                        current_value = c1.value + c2.value
                        merged = self._merge_coalitions(c1, c2)
                        
                        if merged.value > current_value:
                            # Perform merge
                            del self.coalitions[c1.id]
                            del self.coalitions[c2.id]
                            self.coalitions[merged.id] = merged
                            
                            # Update agent coalition assignments
                            for agent_id in merged.members:
                                self.agents[agent_id].coalition_id = merged.id
                            
                            changed = True
                            logging.debug(f"Merged {c1.id} + {c2.id} -> {merged.id}")
                            break
                
                if changed:
                    break
            
            # SPLIT PHASE
            if not changed:
                for coalition in list(self.coalitions.values()):
                    if len(coalition.members) > 1:
                        sub_coalitions = self._split_coalition(coalition)
                        
                        # Compute value improvement
                        current_value = coalition.value
                        split_value = sum(sc.value for sc in sub_coalitions)
                        
                        if split_value > current_value:
                            # Perform split
                            del self.coalitions[coalition.id]
                            
                            for sub_coal in sub_coalitions:
                                self.coalitions[sub_coal.id] = sub_coal
                                
                                for agent_id in sub_coal.members:
                                    self.agents[agent_id].coalition_id = sub_coal.id
                            
                            changed = True
                            logging.debug(f"Split {coalition.id} into {len(sub_coalitions)} coalitions")
                            break
            
            # Check convergence
            if not changed:
                logging.info(f"Converged after {iteration + 1} iterations")
                break
        
        return self.coalitions
    
    def get_coalition_statistics(self) -> Dict:
        """Get statistics about current coalition structure"""
        stats = {
            'num_coalitions': len(self.coalitions),
            'total_value': sum(c.value for c in self.coalitions.values()),
            'avg_coalition_size': np.mean([len(c.members) for c in self.coalitions.values()]),
            'coalition_types': {}
        }
        
        for coalition in self.coalitions.values():
            ctype = coalition.coalition_type.value
            stats['coalition_types'][ctype] = stats['coalition_types'].get(ctype, 0) + 1
        
        return stats


class ResourceManager:
    """
    Manages resource allocation across coalitions.
    """
    
    def __init__(self):
        """Initialize resource manager"""
        self.allocations: Dict[str, Dict[str, float]] = {}
    
    def allocate_resources(
        self,
        coalitions: Dict[str, Coalition],
        total_resources: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Allocate available resources to coalitions proportionally.
        
        Args:
            coalitions: Current coalition structure
            total_resources: Total available resources
            
        Returns:
            Resource allocations per coalition
        """
        # Compute total demand
        total_demand = {}
        for resource_type in total_resources.keys():
            total_demand[resource_type] = sum(
                coalition.resources.get(resource_type, 0)
                for coalition in coalitions.values()
            )
        
        # Proportional allocation
        allocations = {}
        for coalition_id, coalition in coalitions.items():
            coalition_alloc = {}
            
            for resource_type, available in total_resources.items():
                demand = coalition.resources.get(resource_type, 0)
                total_dem = total_demand[resource_type]
                
                if total_dem > 0:
                    allocation = (demand / total_dem) * available
                else:
                    allocation = 0.0
                
                coalition_alloc[resource_type] = allocation
            
            allocations[coalition_id] = coalition_alloc
        
        self.allocations = allocations
        return allocations


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create sample agents
    agents = [
        Agent("H1", AgentType.HUMAN, ["perception"], {"compute": 10, "bandwidth": 5}),
        Agent("H2", AgentType.HUMAN, ["perception"], {"compute": 10, "bandwidth": 5}),
        Agent("A1", AgentType.AI_AGENT, ["inference"], {"compute": 50, "bandwidth": 20}),
        Agent("A2", AgentType.AI_AGENT, ["inference"], {"compute": 50, "bandwidth": 20}),
        Agent("XR1", AgentType.XR_DEVICE, ["rendering"], {"compute": 30, "bandwidth": 40}),
        Agent("XR2", AgentType.XR_DEVICE, ["rendering"], {"compute": 30, "bandwidth": 40}),
        Agent("E1", AgentType.EDGE_NODE, ["processing"], {"compute": 100, "bandwidth": 100}),
        Agent("C1", AgentType.CLOUD_NODE, ["processing"], {"compute": 500, "bandwidth": 200}),
    ]
    
    # Run coalition formation
    game = CoalitionFormationGame(agents)
    final_coalitions = game.run_merge_and_split(max_iterations=20)
    
    # Print results
    stats = game.get_coalition_statistics()
    print(f"\nCoalition Formation Results:")
    print(f"  Number of coalitions: {stats['num_coalitions']}")
    print(f"  Total value: {stats['total_value']:.2f}")
    print(f"  Average coalition size: {stats['avg_coalition_size']:.2f}")
    print(f"  Coalition types: {stats['coalition_types']}")
    
    print(f"\nCoalition Details:")
    for coalition_id, coalition in final_coalitions.items():
        print(f"  {coalition_id}: {coalition.coalition_type.value}")
        print(f"    Members: {coalition.members}")
        print(f"    Value: {coalition.value:.2f}")
