import React, { useState, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import { Layers, Filter, ArrowRight, Activity, AlertTriangle, RefreshCw } from 'lucide-react';

// ============================================================================
// TASK 1: DATA STRUCTURE & SYNTHETIC MOCK DATA GENERATOR
// ============================================================================

/**
 * Severity Color Mapping consistent with DeepGuard app conventions:
 * info: Blue (#3B82F6), warning: Yellow (#F59E0B), high: Orange (#F97316), critical: Red (#EF4444)
 */
const SEVERITY_COLORS = {
  info: '#3B82F6',
  warning: '#F59E0B',
  high: '#F97316',
  critical: '#EF4444'
};

const SEVERITY_WEIGHTS = {
  info: 1,
  warning: 2,
  high: 3,
  critical: 4
};

const REGIONS = [
  { code: 'REG-NORTH', name: 'North Power Grid', baseAngle: 0 },
  { code: 'REG-SOUTH', name: 'South Power Grid', baseAngle: (2 * Math.PI) / 5 },
  { code: 'REG-EAST', name: 'East Power Grid', baseAngle: (4 * Math.PI) / 5 },
  { code: 'REG-WEST', name: 'West Power Grid', baseAngle: (6 * Math.PI) / 5 },
  { code: 'REG-CENTRAL', name: 'Central Urban Grid', baseAngle: (8 * Math.PI) / 5 }
];

const CONNECTION_TYPES = ['Single Phase', 'Three Phase', 'Commercial High Load'];
const TARIFF_CATEGORIES = ['Residential', 'Commercial', 'Industrial'];

/**
 * Mock data generator matching real API contracts and ~8.53% theft prevalence
 * tagged with data_source: "synthetic_demo"
 */
function generateNetworkData() {
  const regions = [];
  const feeders = [];
  const customers = [];

  let customerCounter = 1000;

  REGIONS.forEach((reg, rIdx) => {
    // 3 Feeder lines per region
    const regionFeeders = [];
    const R_REGION = 32;
    const regX = Math.cos(reg.baseAngle) * R_REGION;
    const regZ = Math.sin(reg.baseAngle) * R_REGION;
    const regY = Math.sin(rIdx * 1.5) * 3;

    const regionNode = {
      id: reg.code,
      type: 'region',
      name: reg.name,
      region_code: reg.code,
      position: [regX, regY, regZ],
      feeders_count: 3,
      data_source: 'synthetic_demo'
    };

    for (let f = 1; f <= 3; f++) {
      const feederCode = `FDR-${reg.code.split('-')[1].charAt(0)}${f.toString().padStart(2, '0')}`;
      const fAngle = reg.baseAngle + ((f - 2) * Math.PI) / 6;
      const R_FEEDER = 14;
      
      const feederX = regX + Math.cos(fAngle) * R_FEEDER;
      const feederZ = regZ + Math.sin(fAngle) * R_FEEDER;
      const feederY = regY + (f - 2) * 2;

      const feederNode = {
        id: feederCode,
        type: 'feeder',
        feeder_line: feederCode,
        region_code: reg.code,
        position: [feederX, feederY, feederZ],
        parent_id: reg.code,
        data_source: 'synthetic_demo'
      };

      // 20-30 customers per feeder line
      const numCust = 22 + Math.floor(Math.random() * 10);
      const feederCustomers = [];

      for (let c = 0; c < numCust; c++) {
        customerCounter++;
        const meterId = `MTR-${customerCounter}`;
        
        // Distribute risk matching ~8.53% theft prevalence
        const rand = Math.random();
        let severity = 'info';
        let riskScore = 0.05 + Math.random() * 0.25;

        if (rand > 0.97) {
          severity = 'critical';
          riskScore = 0.86 + Math.random() * 0.12;
        } else if (rand > 0.915) {
          severity = 'high';
          riskScore = 0.66 + Math.random() * 0.19;
        } else if (rand > 0.75) {
          severity = 'warning';
          riskScore = 0.31 + Math.random() * 0.34;
        }

        const cAngle = (c / numCust) * Math.PI * 2;
        const R_CUST = 5.5 + (c % 3) * 1.2;
        const custX = feederX + Math.cos(cAngle) * R_CUST;
        const custZ = feederZ + Math.sin(cAngle) * R_CUST;
        const custY = feederY + Math.sin(cAngle * 2) * 1.8;

        const custNode = {
          id: customerCounter,
          meter_id: meterId,
          name: `Customer ${customerCounter}`,
          type: 'customer',
          connection_type: CONNECTION_TYPES[c % CONNECTION_TYPES.length],
          tariff_category: TARIFF_CATEGORIES[c % TARIFF_CATEGORIES.length],
          feeder_line: feederCode,
          region_code: reg.code,
          sanctioned_load_kw: parseFloat((1.5 + Math.random() * 25).toFixed(1)),
          risk_score: parseFloat(riskScore.toFixed(3)),
          severity: severity,
          status: severity === 'critical' || severity === 'high' ? 'open' : 'resolved',
          position: [custX, custY, custZ],
          parent_id: feederCode,
          data_source: 'synthetic_demo'
        };

        feederCustomers.push(custNode);
        customers.push(custNode);
      }

      // Compute Feeder aggregates
      const feederWorstSev = feederCustomers.reduce((acc, curr) => {
        return SEVERITY_WEIGHTS[curr.severity] > SEVERITY_WEIGHTS[acc] ? curr.severity : acc;
      }, 'info');

      feederNode.severity = feederWorstSev;
      feederNode.total_customers = feederCustomers.length;
      feederNode.high_risk_count = feederCustomers.filter(c => c.severity === 'high' || c.severity === 'critical').length;
      feederNode.max_risk = Math.max(...feederCustomers.map(c => c.risk_score));

      regionFeeders.push(feederNode);
      feeders.push(feederNode);
    }

    // Compute Region aggregates
    const regWorstSev = regionFeeders.reduce((acc, curr) => {
      return SEVERITY_WEIGHTS[curr.severity] > SEVERITY_WEIGHTS[acc] ? curr.severity : acc;
    }, 'info');

    regionNode.severity = regWorstSev;
    regionNode.total_feeders = regionFeeders.length;
    regionNode.total_customers = regionFeeders.reduce((sum, f) => sum + f.total_customers, 0);

    regions.push(regionNode);
  });

  return { regions, feeders, customers };
}

// ============================================================================
// TASK 2 & 3: 3D THREE.JS COMPONENTS (NODES, EDGES, HOVER, CAMERA CONTROLS)
// ============================================================================

/**
 * Animated Pulse Ring for High/Critical Risk Nodes
 */
function PulseRing({ position, color }) {
  const meshRef = useRef();

  useFrame(({ clock }) => {
    if (meshRef.current) {
      const scale = 1 + Math.sin(clock.getElapsedTime() * 3) * 0.25;
      meshRef.current.scale.set(scale, scale, scale);
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      <ringGeometry args={[1.8, 2.3, 32]} />
      <meshBasicMaterial color={color} transparent opacity={0.35} side={THREE.DoubleSide} />
    </mesh>
  );
}

/**
 * 3D Node Mesh (Region, Feeder, or Customer)
 */
function NodeMesh({ node, isHovered, isSelected, onHover, onClick }) {
  const meshRef = useRef();
  const color = SEVERITY_COLORS[node.severity] || '#94A3B8';

  // Node size hierarchy: Region (2.4) > Feeder (1.5) > Customer (0.55)
  const size = useMemo(() => {
    if (node.type === 'region') return 2.4;
    if (node.type === 'feeder') return 1.5;
    return 0.55;
  }, [node.type]);

  useFrame(() => {
    if (meshRef.current && (isHovered || isSelected)) {
      meshRef.current.rotation.y += 0.02;
    }
  });

  return (
    <group position={node.position}>
      {/* Pulse effect for critical nodes */}
      {(node.severity === 'critical' || node.severity === 'high') && (
        <PulseRing position={[0, 0, 0]} color={color} />
      )}

      {/* Main Node Geometry */}
      <mesh
        ref={meshRef}
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover(node);
        }}
        onPointerOut={(e) => {
          e.stopPropagation();
          onHover(null);
        }}
        onClick={(e) => {
          e.stopPropagation();
          onClick(node);
        }}
      >
        {node.type === 'region' ? (
          <icosahedronGeometry args={[size, 2]} />
        ) : node.type === 'feeder' ? (
          <dodecahedronGeometry args={[size, 1]} />
        ) : (
          <sphereGeometry args={[size, 16, 16]} />
        )}

        <meshStandardMaterial
          color={color}
          roughness={0.2}
          metalness={0.6}
          emissive={color}
          emissiveIntensity={isHovered || isSelected ? 0.6 : 0.25}
          wireframe={node.type === 'region'}
        />
      </mesh>

      {/* Node 3D Text Label for Region and Feeder nodes */}
      {(node.type === 'region' || node.type === 'feeder') && (
        <Html position={[0, size + 1.2, 0]} center distanceFactor={60}>
          <div
            className={`px-2.5 py-1 rounded-md text-[11px] font-bold tracking-wider uppercase border whitespace-nowrap backdrop-blur-md shadow-lg pointer-events-none transition-all ${
              node.type === 'region'
                ? 'bg-slate-950/80 text-slate-100 border-slate-700'
                : 'bg-slate-900/80 text-slate-300 border-slate-800'
            }`}
          >
            {node.type === 'region' ? node.name : node.feeder_line}
            <span className="ml-1.5 text-[9px] opacity-75 font-mono">
              ({node.type === 'region' ? `${node.total_customers} cust` : `${node.high_risk_count} alert`})
            </span>
          </div>
        </Html>
      )}
    </group>
  );
}

/**
 * Low-opacity Connecting Edges between Parent & Child Nodes
 */
function ConnectionEdges({ edges }) {
  return (
    <group>
      {edges.map((edge, idx) => (
        <Line
          key={`edge-${idx}`}
          points={[edge.start, edge.end]}
          color={edge.color || '#475569'}
          lineWidth={edge.type === 'region-feeder' ? 1.5 : 0.8}
          transparent
          opacity={edge.type === 'region-feeder' ? 0.25 : 0.15}
        />
      ))}
    </group>
  );
}

/**
 * Camera Controller for smooth drill-down zooming into selected clusters
 */
function CameraRig({ targetPos }) {
  const controlsRef = useRef();

  useFrame((state) => {
    if (targetPos && controlsRef.current) {
      state.camera.lookAt(targetPos[0], targetPos[1], targetPos[2]);
    }
  });

  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping
      dampingFactor={0.05}
      minDistance={10}
      maxDistance={120}
      maxPolarAngle={Math.PI / 2 + 0.1} // Constrain camera so user cannot scroll into an empty void under the grid
    />
  );
}

// ============================================================================
// MAIN PAGE COMPONENT: NetworkRiskMap
// ============================================================================

const NetworkRiskMap = () => {
  const navigate = useNavigate();

  // Load synthetic dataset
  const networkData = useMemo(() => generateNetworkData(), []);
  
  // State management
  const [selectedFeeder, setSelectedFeeder] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [viewMode, setViewMode] = useState('feeder_aggregate'); // 'feeder_aggregate' | 'full_grid'
  const [severityFilter, setSeverityFilter] = useState('all'); // 'all' | 'critical' | 'high' | 'warning' | 'info'
  const [cameraTarget, setCameraTarget] = useState([0, 0, 0]);

  // Filtered nodes based on viewMode and severityFilter
  const visibleCustomers = useMemo(() => {
    let custs = networkData.customers;

    // Task 4 LOD Strategy: Default to feeder aggregate view, render customers when feeder is selected
    if (viewMode === 'feeder_aggregate') {
      if (!selectedFeeder) return [];
      custs = custs.filter(c => c.feeder_line === selectedFeeder.feeder_line);
    }

    if (severityFilter !== 'all') {
      custs = custs.filter(c => c.severity === severityFilter);
    }

    return custs;
  }, [networkData, viewMode, selectedFeeder, severityFilter]);

  // Edges definition
  const edges = useMemo(() => {
    const edgeList = [];

    // Region -> Feeder Edges
    networkData.feeders.forEach((feeder) => {
      const parentReg = networkData.regions.find((r) => r.id === feeder.parent_id);
      if (parentReg) {
        edgeList.push({
          start: parentReg.position,
          end: feeder.position,
          type: 'region-feeder',
          color: SEVERITY_COLORS[feeder.severity]
        });
      }
    });

    // Feeder -> Customer Edges
    visibleCustomers.forEach((cust) => {
      const parentFeeder = networkData.feeders.find((f) => f.id === cust.parent_id);
      if (parentFeeder) {
        edgeList.push({
          start: parentFeeder.position,
          end: cust.position,
          type: 'feeder-customer',
          color: SEVERITY_COLORS[cust.severity]
        });
      }
    });

    return edgeList;
  }, [networkData, visibleCustomers]);

  // Handle Node Selection / Drill Down
  const handleNodeClick = (node) => {
    if (node.type === 'customer') {
      // Task 3: Navigate to existing Customer Detail view
      navigate(`/customer/${node.id}`);
    } else if (node.type === 'feeder') {
      setSelectedFeeder(node);
      setCameraTarget(node.position);
    } else if (node.type === 'region') {
      setSelectedRegion(node);
      setSelectedFeeder(null);
      setCameraTarget(node.position);
    }
  };

  const handleResetFocus = () => {
    setSelectedFeeder(null);
    setSelectedRegion(null);
    setCameraTarget([0, 0, 0]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] bg-dark-bg text-slate-100 overflow-hidden relative">
      
      {/* ────────────────────────────────────────────────────────────────────
          TASK 5: SYNTHETIC DEMO DATA BANNER & HEADER
      ────────────────────────────────────────────────────────────────────── */}
      <div className="px-6 py-4 bg-slate-900/60 border-b border-dark-border flex flex-col md:flex-row md:items-center justify-between gap-4 z-10">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                3D Network Risk Topology
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  Spatial View
                </span>
              </h1>
              <p className="text-xs text-dark-muted mt-0.5">
                Hierarchical grid risk visualization (Region → Feeder Line → Customer)
              </p>
            </div>
          </div>
        </div>

        {/* View Mode & Filter Controls */}
        <div className="flex items-center flex-wrap gap-3">
          {/* Scale LOD Selector */}
          <div className="flex bg-slate-800/80 p-1 rounded-xl border border-dark-border text-xs">
            <button
              onClick={() => setViewMode('feeder_aggregate')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                viewMode === 'feeder_aggregate'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Feeder Drill-Down (Scale Optimized)
            </button>
            <button
              onClick={() => setViewMode('full_grid')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                viewMode === 'full_grid'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Show All Demo Nodes ({networkData.customers.length})
            </button>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center space-x-1 bg-slate-800/80 px-2 py-1 rounded-xl border border-dark-border text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-1 mr-1" />
            {['all', 'critical', 'high', 'warning', 'info'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-2.5 py-1 rounded-lg capitalize font-semibold transition-all ${
                  severityFilter === sev
                    ? 'bg-slate-700 text-slate-100 border border-slate-600'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Reset Focus */}
          <button
            onClick={handleResetFocus}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 border border-dark-border transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset View</span>
          </button>
        </div>
      </div>

      {/* ⚠️ TASK 5: Synthetic Demo Data Banner */}
      <div className="bg-amber-950/40 border-b border-amber-500/20 px-6 py-2 flex items-center justify-between text-xs text-amber-200/90 z-10">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>
            <strong className="text-amber-300">NOTICE: Running on Synthetic Demo Data</strong> — Tagged with <code className="bg-amber-900/50 px-1 py-0.5 rounded text-amber-200">data_source: "synthetic_demo"</code> matching SGCC dataset 8.5% theft prevalence ratio.
          </span>
        </div>
        {selectedFeeder && (
          <span className="bg-amber-900/40 px-2.5 py-0.5 rounded-md border border-amber-500/30 text-[11px] font-mono">
            Active Feeder Focus: <strong>{selectedFeeder.feeder_line}</strong> ({selectedFeeder.region_code})
          </span>
        )}
      </div>

      {/* ────────────────────────────────────────────────────────────────────
          MAIN 3D CANVAS AREA & OVERLAYS
      ────────────────────────────────────────────────────────────────────── */}
      <div className="flex-1 relative w-full h-full bg-gradient-to-b from-slate-950 via-slate-900 to-dark-bg">
        
        <Canvas
          camera={{ position: [0, 45, 75], fov: 50 }}
          gl={{ antialias: true }}
          onPointerMissed={() => setHoveredNode(null)}
        >
          <ambientLight intensity={0.7} />
          <directionalLight position={[20, 50, 20]} intensity={1.2} />
          <pointLight position={[-20, -20, -20]} intensity={0.5} />

          {/* Render Region Nodes */}
          {networkData.regions.map((reg) => (
            <NodeMesh
              key={reg.id}
              node={reg}
              isHovered={hoveredNode?.id === reg.id}
              isSelected={selectedRegion?.id === reg.id}
              onHover={setHoveredNode}
              onClick={handleNodeClick}
            />
          ))}

          {/* Render Feeder Line Nodes */}
          {networkData.feeders.map((feeder) => (
            <NodeMesh
              key={feeder.id}
              node={feeder}
              isHovered={hoveredNode?.id === feeder.id}
              isSelected={selectedFeeder?.id === feeder.id}
              onHover={setHoveredNode}
              onClick={handleNodeClick}
            />
          ))}

          {/* Render Customer Leaf Nodes (Driven by Task 4 LOD strategy) */}
          {visibleCustomers.map((cust) => (
            <NodeMesh
              key={cust.id}
              node={cust}
              isHovered={hoveredNode?.id === cust.id}
              isSelected={false}
              onHover={setHoveredNode}
              onClick={handleNodeClick}
            />
          ))}

          {/* Render Connection Edges */}
          <ConnectionEdges edges={edges} />

          {/* Orbit & Camera Controls */}
          <CameraRig targetPos={cameraTarget} />
        </Canvas>

        {/* ──────────────────────────────────────────────────────────────────
            TASK 3: HOVER TOOLTIP / DETAILS OVERLAY
        ──────────────────────────────────────────────────────────────────── */}
        {hoveredNode && (
          <div className="absolute top-6 left-6 z-20 w-80 glass-panel p-4 rounded-2xl border border-slate-700/60 shadow-2xl backdrop-blur-xl animate-fadeIn">
            <div className="flex items-start justify-between border-b border-dark-border pb-3 mb-3">
              <div>
                <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400">
                  {hoveredNode.type} Node Details
                </span>
                <h3 className="text-lg font-extrabold text-white mt-0.5">
                  {hoveredNode.type === 'customer' ? hoveredNode.meter_id : hoveredNode.type === 'feeder' ? hoveredNode.feeder_line : hoveredNode.name}
                </h3>
              </div>
              <span
                className="px-2.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-wide border"
                style={{
                  color: SEVERITY_COLORS[hoveredNode.severity],
                  backgroundColor: `${SEVERITY_COLORS[hoveredNode.severity]}15`,
                  borderColor: `${SEVERITY_COLORS[hoveredNode.severity]}40`
                }}
              >
                {hoveredNode.severity}
              </span>
            </div>

            {hoveredNode.type === 'customer' ? (
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Risk Score Index:</span>
                  <span className="font-mono font-bold text-white">{(hoveredNode.risk_score * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Region Code:</span>
                  <span className="font-semibold text-slate-200">{hoveredNode.region_code}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Feeder Line:</span>
                  <span className="font-semibold text-slate-200">{hoveredNode.feeder_line}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Tariff Category:</span>
                  <span className="text-slate-300">{hoveredNode.tariff_category}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Sanctioned Load:</span>
                  <span className="font-semibold text-blue-400">{hoveredNode.sanctioned_load_kw} kW</span>
                </div>

                <div className="pt-3">
                  <button
                    onClick={() => navigate(`/customer/${hoveredNode.id}`)}
                    className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-3 rounded-xl transition-all shadow-md shadow-blue-600/20"
                  >
                    <span>View Customer Analytics</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Associated Region:</span>
                  <span className="font-semibold text-slate-200">{hoveredNode.region_code}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Connected Customers:</span>
                  <span className="font-bold text-white">{hoveredNode.total_customers || 0}</span>
                </div>
                {hoveredNode.type === 'feeder' && (
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">High Risk Alerts:</span>
                    <span className="font-bold text-orange-400">{hoveredNode.high_risk_count}</span>
                  </div>
                )}
                <p className="text-[11px] text-slate-400 italic pt-1">
                  Click to focus camera and expand feeder line node hierarchy.
                </p>
              </div>
            )}
          </div>
        )}

        {/* ──────────────────────────────────────────────────────────────────
            TASK 4: REAL-WORLD SCALE CALLOUT & LOD STRATEGY
        ──────────────────────────────────────────────────────────────────── */}
        <div className="absolute bottom-6 left-6 z-20 max-w-md glass-panel p-4 rounded-2xl border border-slate-800 text-xs text-slate-300">
          <div className="flex items-center space-x-2 text-slate-100 font-bold mb-1">
            <Activity className="w-4 h-4 text-blue-400" />
            <span>Scale Reality & LOD Strategy</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            The full SGCC dataset contains <strong>42,372 customers</strong>. Rendering 42k individual 3D nodes simultaneously leads to GPU frame drops. DeepGuard aggregates at the <strong>Region</strong> and <strong>Feeder Line</strong> levels, expanding individual customer nodes on demand when a feeder is selected.
          </p>
        </div>

        {/* ──────────────────────────────────────────────────────────────────
            TASK 5: CONTROL ROOM LEGEND OVERLAY
        ──────────────────────────────────────────────────────────────────── */}
        <div className="absolute bottom-6 right-6 z-20 glass-panel p-4 rounded-2xl border border-slate-800 text-xs space-y-3 min-w-[200px]">
          <h4 className="font-bold text-slate-200 border-b border-slate-800 pb-2">
            Severity & Node Legend
          </h4>

          {/* Color Legend */}
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-rose-500 shadow shadow-rose-500/50" />
              <span className="text-slate-300">Critical Theft Hazard</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-orange-500 shadow shadow-orange-500/50" />
              <span className="text-slate-300">High Risk Anomaly</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-amber-500 shadow shadow-amber-500/50" />
              <span className="text-slate-300">Warning / Suspect</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-blue-500 shadow shadow-blue-500/50" />
              <span className="text-slate-300">Info / Normal</span>
            </div>
          </div>

          {/* Node Hierarchy Sizing */}
          <div className="pt-2 border-t border-slate-800 space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Hierarchy Size</span>
            <div className="text-[11px] text-slate-400 flex justify-between">
              <span>Region Node</span>
              <span className="font-mono text-slate-200">Large Wireframe</span>
            </div>
            <div className="text-[11px] text-slate-400 flex justify-between">
              <span>Feeder Line</span>
              <span className="font-mono text-slate-200">Medium Poly</span>
            </div>
            <div className="text-[11px] text-slate-400 flex justify-between">
              <span>Customer</span>
              <span className="font-mono text-slate-200">Small Sphere</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default NetworkRiskMap;
