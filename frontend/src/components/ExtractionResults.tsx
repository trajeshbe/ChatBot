import { Building2, MapPin, Users, Car, TreePine } from 'lucide-react'

interface DocumentExtractionResult {
  // Project Metadata (11 fields)
  project_name?: string
  address?: string
  project_status?: string
  storeys?: number
  gross_floor_area?: number
  site_area?: number
  zoning?: string
  heritage_designation?: string
  architect?: string
  developer?: string
  planning_consultant?: string

  // Building Information (7 fields)
  residential_units?: number
  unit_types?: string[]
  commercial_uses?: string[]
  amenities?: string[]
  parking_levels?: number
  parking_spaces?: number
  public_realm_features?: string[]

  // Metadata
  fields_extracted: number
  total_fields: number
  extraction_method?: string
  processing_time_ms?: number
}

interface ExtractionResultsProps {
  data: DocumentExtractionResult
}

const FieldCard = ({
  label,
  value,
  unit,
  isArray = false
}: {
  label: string
  value: any
  unit?: string
  isArray?: boolean
}) => {
  const hasValue = value !== null && value !== undefined && value !== '' && (!isArray || (Array.isArray(value) && value.length > 0))

  return (
    <div
      className={`p-4 rounded-lg border ${
        hasValue
          ? 'bg-emerald-50 border-emerald-200'
          : 'bg-slate-50 border-slate-200'
      }`}
    >
      <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-1">
        {label}
      </div>
      <div
        className={`text-lg font-bold ${
          hasValue ? 'text-emerald-700' : 'text-slate-400'
        }`}
      >
        {hasValue ? (
          isArray && Array.isArray(value) ? (
            <div className="flex flex-wrap gap-1 mt-1">
              {value.map((item, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-1 bg-white border border-emerald-300 rounded text-emerald-700 font-normal"
                >
                  {item}
                </span>
              ))}
            </div>
          ) : (
            `${value}${unit || ''}`
          )
        ) : (
          'N/A'
        )}
      </div>
    </div>
  )
}

export default function ExtractionResults({ data }: ExtractionResultsProps) {
  return (
    <div className="space-y-6">
      {/* Project Overview Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-bold text-slate-900">Project Overview</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="md:col-span-2 lg:col-span-3">
            <FieldCard label="Project Name" value={data.project_name} />
          </div>

          <div className="md:col-span-2">
            <FieldCard label="Address" value={data.address} />
          </div>

          <FieldCard label="Project Status" value={data.project_status} />

          <FieldCard label="Storeys" value={data.storeys} />

          <FieldCard
            label="Gross Floor Area"
            value={data.gross_floor_area}
            unit=" m²"
          />

          <FieldCard
            label="Site Area"
            value={data.site_area}
            unit=" m²"
          />
        </div>
      </div>

      {/* Regulatory Information Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <MapPin className="w-5 h-5 text-purple-600" />
          <h2 className="text-xl font-bold text-slate-900">Regulatory Information</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FieldCard label="Zoning" value={data.zoning} />

          <div className="md:col-span-2">
            <FieldCard
              label="Heritage Designation"
              value={data.heritage_designation}
            />
          </div>
        </div>
      </div>

      {/* Project Team Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-orange-600" />
          <h2 className="text-xl font-bold text-slate-900">Project Team</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FieldCard label="Architect" value={data.architect} />

          <FieldCard label="Developer" value={data.developer} />

          <FieldCard
            label="Planning Consultant"
            value={data.planning_consultant}
          />
        </div>
      </div>

      {/* Building Information Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="w-5 h-5 text-teal-600" />
          <h2 className="text-xl font-bold text-slate-900">Building Information</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <FieldCard
            label="Residential Units"
            value={data.residential_units}
          />

          <div className="md:col-span-2">
            <FieldCard
              label="Unit Types"
              value={data.unit_types}
              isArray={true}
            />
          </div>

          <div className="md:col-span-2 lg:col-span-3">
            <FieldCard
              label="Commercial Uses"
              value={data.commercial_uses}
              isArray={true}
            />
          </div>

          <div className="md:col-span-2 lg:col-span-3">
            <FieldCard
              label="Amenities"
              value={data.amenities}
              isArray={true}
            />
          </div>
        </div>
      </div>

      {/* Parking Information Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Car className="w-5 h-5 text-indigo-600" />
          <h2 className="text-xl font-bold text-slate-900">Parking</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FieldCard
            label="Parking Levels"
            value={data.parking_levels}
          />

          <FieldCard
            label="Parking Spaces"
            value={data.parking_spaces}
          />
        </div>
      </div>

      {/* Public Realm Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <TreePine className="w-5 h-5 text-green-600" />
          <h2 className="text-xl font-bold text-slate-900">Public Realm</h2>
        </div>

        <div className="grid grid-cols-1 gap-4">
          <FieldCard
            label="Public Realm Features"
            value={data.public_realm_features}
            isArray={true}
          />
        </div>
      </div>

      {/* Extraction Summary */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="text-sm font-semibold text-blue-900 mb-2">
          Extraction Summary
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-blue-700">Fields Extracted:</span>{' '}
            <span className="font-semibold text-blue-900">
              {data.fields_extracted}/{data.total_fields}
            </span>
          </div>
          <div>
            <span className="text-blue-700">Completion:</span>{' '}
            <span className="font-semibold text-blue-900">
              {((data.fields_extracted / data.total_fields) * 100).toFixed(0)}%
            </span>
          </div>
          {data.extraction_method && (
            <div>
              <span className="text-blue-700">Method:</span>{' '}
              <span className="font-semibold text-blue-900">
                {data.extraction_method}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
