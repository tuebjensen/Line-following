import * as d3 from 'https://cdn.skypack.dev/pin/d3@v7.6.1-1Q0NZ0WZnbYeSjDusJT3/mode=imports,min/optimized/d3.js'
import { Subject, EMPTY, share, map, of, distinctUntilChanged, withLatestFrom, switchMap, tap, fromEvent, merge, combineLatest } from 'https://cdn.skypack.dev/pin/rxjs@v7.5.7-j3yWv9lQY9gNeD9CyX5Y/mode=imports,min/optimized/rxjs.js'
import { initalizeSharedState } from './initalize-shared-state.js'
import { parseMap } from './parse-map.js'
import { findPath } from './pathfinding.js'

const { clientState$, clientStateUpdate$, serverState$, updateClientState, updateServerState } = initalizeSharedState()
 
const nodeLeftClick$ = new Subject()
const nodeRightClick$ = new Subject()

const mapInput = document.getElementById('map-input')
const mapUpdateError = document.getElementById('map-update-error')
const inputtedMap$ = fromEvent(document.getElementById('map-update-form'), 'submit').pipe(
    switchMap((e) => {
        e.preventDefault()
        try {
            mapUpdateError.innerText = ''
            return of({
                map: parseMap(mapInput.value),
                mapStr: mapInput.value
            })
        } catch (err) {
            mapUpdateError.innerText = 'Parsing error: ' + err.message
            return EMPTY
        }
    }),
    share()
)

clientStateUpdate$.subscribe(clientState => {
    if (clientState) {
        mapInput.value = clientState.mapStr
    }
})

inputtedMap$.subscribe(x => console.log('new map', x))

// Update client state from client
merge(
    inputtedMap$.pipe(
        map(({ map, mapStr }) => ({
            map,
            mapStr,
            targetNode: null,
            path: []
        }))
    ),
    nodeLeftClick$.pipe(
        withLatestFrom(clientState$, serverState$),
        map(([node, clientState, serverState]) => ({
            ...clientState,
            targetNode: node.id,
            path: findPath(clientState.map, serverState?.currentNode || 0, node.id)
        }))
    )
).pipe(
    distinctUntilChanged(undefined, JSON.stringify),
).subscribe(clientState => {
    console.log('new client state', clientState)
    updateClientState(clientState)
})

// Update shared state from client
nodeRightClick$.pipe(
    map((node) => ({
        currentNode: node
    }))
).subscribe(serverState => {
    updateServerState(serverState)
})

// Display interface with D3
const svg = d3.select('svg')
const lineGroup = svg.append('g')
const nodeGroup = svg.append('g')

combineLatest([
    serverState$,
    clientState$
]).subscribe(([serverState, clientState]) => {
    d3.select('#blocker').classed('hidden', !!clientState)
    if(!clientState) {
        lineGroup.selectAll('*').remove()
        nodeGroup.selectAll('*').remove()
        return
    }

    const { map, targetNode, path } = clientState
    const { currentNode } = serverState || { currentNode: null }

    // calculate dimensions of the newly displayed map
    const smallestDistance = Math.min(
        ...map.lineSegments.map(l =>
            Math.sqrt((l.start.x - l.end.x)**2 + (l.start.y - l.end.y)**2)
        )
    )
    const nodeRadius = smallestDistance / 2
    
    const minX = Math.min(...map.nodes.map(node => node.x)) - nodeRadius
    const minY = Math.min(...map.nodes.map(node => node.y)) - nodeRadius
    const maxX = Math.max(...map.nodes.map(node => node.x)) + nodeRadius
    const maxY = Math.max(...map.nodes.map(node => node.y)) + nodeRadius
    const width = maxX - minX
    const height = maxY - minY

    // update the display of the line segments
    const line = lineGroup
        .selectAll('.line')
        .data(map.lineSegments)
        .join(
            enter => enter
                .append('line')
        )
        .attr('x1', line => line.start.x)
        .attr('y1', line => line.start.y)
        .attr('x2', line => line.end.x)
        .attr('y2', line => line.end.y)
        .attr('stroke-width', smallestDistance * 0.1)
        .attr('stroke-linecap', 'round')
        .classed('line', true)
        .classed('path-line', line => {
            let start = path.findIndex(node => line.start.id === node)
            let end = path.findIndex(node => line.end.id === node)
            if (start === -1 || end === -1) {
                return false
            }
            return Math.abs(start - end) === 1
        })

    // update the display of the nodes
    const node = nodeGroup
        .selectAll('.node')
        .data(map.nodes, node => node.id)
        .join(
            enter => enter
                .append('g')
                .call(g => {
                    g
                        .append('circle')
                    g
                        .append('text')
                        .attr('dominant-baseline', 'central')
                        .attr('text-anchor', 'middle')
                        .text(node => node.id)
                })
        )
        .attr('transform', node => `translate(${node.x},${node.y}) scale(${node.isPossibleDestination ? 1 : 0.5})`)
        .classed('destination', node => node.isPossibleDestination)
        .classed('current-destination', node => (console.log(node.id, targetNode), node.id === targetNode))
        .classed('current', node => node.id === currentNode)
        .classed('node', true)

    nodeGroup.selectAll('.node.destination')
        .on('click', function(event, datum) {
            nodeLeftClick$.next(datum)
        })
    
    node
        .select('circle')
        .attr('r', smallestDistance * 0.4)

    node
        .select('text')
        .attr('font-size', smallestDistance * 0.4 + 'px')

    // resize viewBox so that all the nodes fit
    svg.attr('viewBox', `${minX} ${minY} ${width} ${height}`)
})
