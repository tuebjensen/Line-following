import * as d3 from 'https://cdn.skypack.dev/pin/d3@v7.6.1-1Q0NZ0WZnbYeSjDusJT3/mode=imports,min/optimized/d3.js'
import { Subject, EMPTY, merge, map, of, concatMap, switchMap, fromEvent, tap } from 'https://cdn.skypack.dev/pin/rxjs@v7.5.7-j3yWv9lQY9gNeD9CyX5Y/mode=imports,min/optimized/rxjs.js'
import { initalizeSharedState } from './initalize-shared-state.js'
import { parseMap } from './parse-map.js'
import { findPath } from './pathfinding.js'

const { sharedState$, updateClientState, updateServerState } = initalizeSharedState()
 
const nodeLeftClick$ = new Subject()
const nodeRightClick$ = new Subject()

const mapInput = document.getElementById('map-input')
const mapUpdateError = document.getElementById('map-update-error')
const inputtedMap$ = fromEvent(document.getElementById('map-update-form'), 'submit').pipe(
    concatMap((e) => {
        console.log(e)
        e.preventDefault()
        try {
            return of(parseMap(mapInput.value))
        } catch (err) {
            mapUpdateError.innerText = 'Parsing error: ' + err.message
            return EMPTY
        }
    })
)

// Update shared state
sharedState$.pipe(
    tap(console.log),
    switchMap(sharedState =>
        merge(
            inputtedMap$.pipe(
                map(map => ({
                    map,
                    targetNode: null,
                    path: []
                }))
            ),
            nodeLeftClick$.pipe(
                map(targetNode => ({
                    targetNode,
                    path: findPath(
                        sharedState.clientState.map,
                        sharedState.serverState.currentNode,
                        targetNode
                    )
                }))
            )
        ).pipe(
            map((newClientState) => ({
                ...sharedState.clientState,
                ...newClientState
            }))
        )
    )
).subscribe(clientState => {
    console.log(clientState)
    updateClientState(clientState)
})

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

sharedState$.subscribe((state) => {
    if(!state.clientState) {
        lineGroup.selectAll('*').remove()
        nodeGroup.selectAll('*').remove()
        return
    }

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
        .classed('node', true)
        .on('click', node => {
            nodeLeftClick$.next(node)
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
