// Graph View for Message Propagation Visualization

class GraphView {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.nodes = [];
        this.edges = [];
        this.currentStep = 0;
        this.maxSteps = 50;
        this.animationFrame = null;
        this.messageParticles = [];
        
        // Resize canvas to fit container
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    resizeCanvas() {
        const container = this.canvas.parentElement;
        const rect = container.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = Math.min(rect.height - 120, 600);
    }
    
    // Initialize graph with personas
    initializeGraph(personas) {
        this.nodes = [];
        this.edges = [];
        this.currentStep = 0;
        this.messageParticles = [];
        
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const radius = Math.min(centerX, centerY) - 60;
        const angleStep = (2 * Math.PI) / personas.length;
        
        // Create nodes in circular layout
        personas.forEach((persona, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            
            this.nodes.push({
                id: persona.id,
                name: persona.name,
                x: x,
                y: y,
                radius: 25,
                state: 'inactive', // inactive, active, engaged
                engagementScore: 0,
                visitCount: 0
            });
        });
        
        // Create fully connected edges
        for (let i = 0; i < this.nodes.length; i++) {
            for (let j = i + 1; j < this.nodes.length; j++) {
                this.edges.push({
                    from: this.nodes[i],
                    to: this.nodes[j],
                    opacity: 0.1
                });
            }
        }
        
        this.render();
    }
    
    // Start message propagation simulation
    async startPropagation(initialMessage) {
        this.currentStep = 0;
        this.messageParticles = [];
        this.messageContent = initialMessage; // Store for LLM calls
        
        // Start from a random node or first node
        const startNode = this.nodes[Math.floor(Math.random() * this.nodes.length)];
        startNode.state = 'active';
        startNode.visitCount = 1;
        
        showNotification('AI personas analyzing message...', 'info');
        
        // Run propagation steps
        for (let step = 0; step < this.maxSteps; step++) {
            this.currentStep = step + 1;
            
            await this.propagateStep();
            
            // Update stats display
            this.updateStats();
            
            // Delay between steps
            await this.sleep(500); // Slightly longer for LLM calls
        }
        
        showNotification('Propagation complete!', 'success');
    }
    
    async propagateStep() {
        // Find all active nodes
        const activeNodes = this.nodes.filter(n => n.state === 'active');
        
        if (activeNodes.length === 0) {
            // If no active nodes, reactivate engaged nodes with low probability
            const engagedNodes = this.nodes.filter(n => n.state === 'engaged');
            if (engagedNodes.length > 0 && Math.random() < 0.3) {
                // 30% chance to re-share from an engaged node
                const randomEngaged = engagedNodes[Math.floor(Math.random() * engagedNodes.length)];
                randomEngaged.state = 'active';
            } else {
                return; // No propagation this step
            }
        }
        
        // Each active node may pass message to neighbors
        const newlyActivated = [];
        
        // Process all active nodes (make LLM calls in parallel for speed)
        const decisions = await Promise.all(
            activeNodes.map(node => this.getLLMDecision(node))
        );
        
        for (let i = 0; i < activeNodes.length; i++) {
            const node = activeNodes[i];
            const decision = decisions[i];
            
            if (decision.engage) {
                node.state = 'engaged';
                node.engagementScore += 1;
                node.engagementReason = decision.reason;
                
                // Number of targets based on priority (high priority = more shares)
                const baseTargets = Math.floor(Math.random() * 2) + 1; // 1-2
                const bonusTarget = decision.priority > 0.7 ? 1 : 0; // +1 if high priority
                const numTargets = baseTargets + bonusTarget;
                
                // Prefer nodes that haven't been reached yet
                const unvisitedTargets = this.nodes.filter(n => n.id !== node.id && n.visitCount === 0);
                const visitedTargets = this.nodes.filter(n => n.id !== node.id && n.visitCount > 0);
                
                // Combine: unvisited first, then visited
                const allTargets = [...unvisitedTargets, ...visitedTargets];
                
                for (let j = 0; j < Math.min(numTargets, allTargets.length); j++) {
                    const targetIndex = Math.min(j, allTargets.length - 1);
                    const target = allTargets[targetIndex];
                    
                    // Animate message particle
                    this.addMessageParticle(node, target);
                    
                    // Activate target if not already engaged
                    if (target.state !== 'engaged') {
                        target.state = 'active';
                        newlyActivated.push(target);
                    }
                    target.visitCount += 1;
                }
            } else {
                // Node doesn't engage - becomes inactive (but keeps visit count)
                node.state = 'inactive';
                node.engagementReason = decision.reason;
            }
        }
        
        // Animate particles
        await this.animateParticles();
    }
    
    async getLLMDecision(node) {
        /**
         * Call backend API to get LLM decision on whether this persona
         * would engage with the message.
         */
        try {
            const response = await fetch(`${API_BASE}/api/views/decide-engagement`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    persona_id: node.id,
                    message: this.messageContent
                })
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`${node.name}: ${data.engage ? '✓' : '✗'} - ${data.reason} (priority: ${data.priority})`);
            
            return {
                engage: data.engage,
                reason: data.reason,
                priority: data.priority
            };
            
        } catch (error) {
            console.error(`Error getting LLM decision for ${node.name}:`, error);
            // Fallback to random on error
            return {
                engage: Math.random() < 0.5,
                reason: "Network error - random decision",
                priority: 0.5
            };
        }
    }
    
    addMessageParticle(from, to) {
        this.messageParticles.push({
            x: from.x,
            y: from.y,
            targetX: to.x,
            targetY: to.y,
            progress: 0,
            speed: 0.08
        });
    }
    
    async animateParticles() {
        return new Promise((resolve) => {
            const animate = () => {
                let allComplete = true;
                
                this.messageParticles.forEach(particle => {
                    if (particle.progress < 1) {
                        particle.progress += particle.speed;
                        allComplete = false;
                    }
                });
                
                this.render();
                
                if (!allComplete) {
                    requestAnimationFrame(animate);
                } else {
                    this.messageParticles = [];
                    resolve();
                }
            };
            
            animate();
        });
    }
    
    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw edges
        this.edges.forEach(edge => {
            this.drawEdge(edge);
        });
        
        // Draw message particles
        this.messageParticles.forEach(particle => {
            if (particle.progress <= 1) {
                const x = particle.x + (particle.targetX - particle.x) * particle.progress;
                const y = particle.y + (particle.targetY - particle.y) * particle.progress;
                
                this.ctx.beginPath();
                this.ctx.arc(x, y, 5, 0, 2 * Math.PI);
                this.ctx.fillStyle = '#f59e0b';
                this.ctx.fill();
                
                // Glow effect
                this.ctx.shadowBlur = 15;
                this.ctx.shadowColor = '#f59e0b';
                this.ctx.arc(x, y, 5, 0, 2 * Math.PI);
                this.ctx.fill();
                this.ctx.shadowBlur = 0;
            }
        });
        
        // Draw nodes
        this.nodes.forEach(node => {
            this.drawNode(node);
        });
    }
    
    drawEdge(edge) {
        this.ctx.beginPath();
        this.ctx.moveTo(edge.from.x, edge.from.y);
        this.ctx.lineTo(edge.to.x, edge.to.y);
        this.ctx.strokeStyle = `rgba(148, 163, 184, ${edge.opacity})`;
        this.ctx.lineWidth = 1;
        this.ctx.stroke();
    }
    
    drawNode(node) {
        // Node circle
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
        
        // Color based on state
        if (node.state === 'active') {
            this.ctx.fillStyle = '#10b981';
            this.ctx.shadowBlur = 15;
            this.ctx.shadowColor = '#10b981';
        } else if (node.state === 'engaged') {
            this.ctx.fillStyle = '#3b82f6';
            this.ctx.shadowBlur = 15;
            this.ctx.shadowColor = '#3b82f6';
        } else {
            this.ctx.fillStyle = '#64748b';
            this.ctx.shadowBlur = 0;
        }
        
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
        
        // Border
        this.ctx.strokeStyle = '#1e293b';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // Label
        this.ctx.fillStyle = '#f1f5f9';
        this.ctx.font = 'bold 12px Inter, sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        // Truncate long names
        let displayName = node.name;
        if (displayName.length > 8) {
            displayName = displayName.substring(0, 7) + '…';
        }
        
        this.ctx.fillText(displayName, node.x, node.y);
        
        // Visit count
        if (node.visitCount > 0) {
            this.ctx.fillStyle = '#f59e0b';
            this.ctx.font = 'bold 10px Inter, sans-serif';
            this.ctx.fillText(node.visitCount, node.x, node.y + node.radius + 12);
        }
    }
    
    updateStats() {
        document.getElementById('currentStep').textContent = `${this.currentStep} / ${this.maxSteps}`;
        
        const engagedCount = this.nodes.filter(n => n.visitCount > 0).length;
        const reachPercent = Math.round((engagedCount / this.nodes.length) * 100);
        
        document.getElementById('reachPercent').textContent = `${reachPercent}%`;
        document.getElementById('engagedCount').textContent = `${engagedCount} / ${this.nodes.length}`;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    reset() {
        this.nodes.forEach(node => {
            node.state = 'inactive';
            node.engagementScore = 0;
            node.visitCount = 0;
        });
        this.currentStep = 0;
        this.messageParticles = [];
        this.updateStats();
        this.render();
    }
}

// Global graph view instance
let graphView = null;

// Initialize graph view when needed
function initializeGraphView(personas) {
    if (!graphView) {
        graphView = new GraphView('graphCanvas');
    }
    graphView.initializeGraph(personas);
}

// Toggle between chat and graph view
function switchViewMode(mode) {
    const chatMessages = document.getElementById('chatMessages');
    const graphView = document.getElementById('graphView');
    const userInput = document.querySelector('.chat-input');
    
    if (mode === 'views') {
        chatMessages.style.display = 'none';
        graphView.style.display = 'flex';
        userInput.style.display = 'flex'; // Keep input for seeding message
    } else {
        chatMessages.style.display = 'flex';
        graphView.style.display = 'none';
        userInput.style.display = 'flex';
    }
}

